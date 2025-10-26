from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4
import shutil
import logging

import astropy.units as u
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.security import OAuth2PasswordRequestForm
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlmodel import delete

# Логгер для модуля
logger = logging.getLogger(__name__)

from .config import settings
from .database import get_session, init_db
from .models import Observation, OrbitSolution, User
from .orbit import derive_orbit, find_closest_approach
from .schemas import (
    ClosestApproach, ComputeResponse, ObservationRead, OrbitElements,
    Token, UserCreate, UserRead
)
from .auth import (
    authenticate_user, create_access_token, get_current_user,
    get_password_hash
)

app = FastAPI(title="Comet Orbit Lab")

app.add_middleware(
    CORSMiddleware,
    allow_origins=[settings.frontend_origin, "http://localhost:5173", "http://127.0.0.1:5173"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

app.mount("/uploads", StaticFiles(directory=settings.upload_dir), name="uploads")


@app.on_event("startup")
def on_startup():
    init_db()
    # Создаем пользователей по умолчанию
    _create_default_users()


def _create_default_users():
    """Создает пользователей admin и user если их еще нет"""
    from .database import engine
    
    with Session(engine) as session:
        # Проверяем существование admin
        admin = session.exec(select(User).where(User.username == "admin")).first()
        if not admin:
            admin = User(
                username="admin",
                hashed_password=get_password_hash("admin")
            )
            session.add(admin)
            logger.info("Created default admin user")
        
        # Проверяем существование user
        user = session.exec(select(User).where(User.username == "user")).first()
        if not user:
            user = User(
                username="user",
                hashed_password=get_password_hash("user")
            )
            session.add(user)
            logger.info("Created default user")
        
        session.commit()


@app.post("/login", response_model=Token)
async def login(
    form_data: OAuth2PasswordRequestForm = Depends(),
    session: Session = Depends(get_session)
):
    """
    Аутентификация пользователя.
    Принимает username и password, возвращает JWT токен.
    """
    user = authenticate_user(session, form_data.username, form_data.password)
    if not user:
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    access_token = create_access_token(data={"sub": user.username})
    return Token(access_token=access_token, token_type="bearer")


@app.post("/register", response_model=UserRead, status_code=status.HTTP_201_CREATED)
async def register(
    user_data: UserCreate,
    session: Session = Depends(get_session)
):
    """
    Регистрация нового пользователя.
    """
    # Проверяем не существует ли пользователь
    existing_user = session.exec(select(User).where(User.username == user_data.username)).first()
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Создаем нового пользователя
    new_user = User(
        username=user_data.username,
        hashed_password=get_password_hash(user_data.password)
    )
    session.add(new_user)
    session.commit()
    session.refresh(new_user)
    
    return UserRead(
        id=new_user.id,
        username=new_user.username,
        created_at=new_user.created_at
    )


@app.get("/me", response_model=UserRead)
async def get_me(current_user: User = Depends(get_current_user)):
    """
    Получить информацию о текущем аутентифицированном пользователе.
    """
    return UserRead(
        id=current_user.id,
        username=current_user.username,
        created_at=current_user.created_at
    )


def _photo_url(obs: Observation) -> str:
    path = Path(obs.photo_path).name
    return f"/uploads/{path}"


def _to_read(obs: Observation) -> ObservationRead:
    return ObservationRead(
        id=obs.id,
        ra_hours=obs.ra_hours,
        dec_degrees=obs.dec_degrees,
        observation_time=obs.observation_time,
        photo_url=_photo_url(obs),
    )


@app.post("/observations", response_model=ObservationRead)
async def create_observation(
    ra_hours: float = Form(...),
    dec_degrees: float = Form(...),
    observation_time: datetime = Form(...),
    photo: UploadFile = File(...),
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user),
):
    if photo.content_type and not photo.content_type.startswith("image/"):
        raise HTTPException(status_code=400, detail="Фото должно быть изображением.")

    filename = f"{uuid4().hex}_{photo.filename}"
    destination = settings.upload_dir / filename

    with destination.open("wb") as dest_file:
        shutil.copyfileobj(photo.file, dest_file)

    observation = Observation(
        ra_hours=ra_hours,
        dec_degrees=dec_degrees,
        observation_time=observation_time,
        photo_path=str(destination),
    )
    session.add(observation)
    session.commit()
    session.refresh(observation)

    return _to_read(observation)


@app.get("/observations", response_model=List[ObservationRead])
def list_observations(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    observations = session.exec(select(Observation).order_by(Observation.observation_time)).all()
    return [_to_read(obs) for obs in observations]


@app.delete("/observations/{obs_id}", status_code=204)
def delete_observation(
    obs_id: int,
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    obs = session.get(Observation, obs_id)
    if not obs:
        raise HTTPException(status_code=404, detail="Наблюдение не найдено")

    # попытка удалить файл фото, если он существует
    try:
        photo_path = Path(obs.photo_path)
        if photo_path.exists():
            photo_path.unlink()
    except Exception as e:
        logger.warning("Failed to remove photo file %s: %s", getattr(photo_path, 'as_posix', lambda: str(photo_path))(), e)

    session.delete(obs)
    session.commit()
    return None


@app.post("/compute", response_model=ComputeResponse)
def compute_orbit(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    observations = session.exec(select(Observation).order_by(Observation.observation_time)).all()
    if len(observations) < 5:
        raise HTTPException(status_code=400, detail="Нужно минимум 5 наблюдений.")

    try:
        orbit = derive_orbit(observations)
        closest_time, distance_km, rel_speed = find_closest_approach(orbit)
    except Exception as e:
        logger.exception("Orbit computation failed")
        raise HTTPException(status_code=500, detail=str(e))

    orbit_data = OrbitElements(
        semi_major_axis_au=float(orbit.a.to(u.AU).value),
        eccentricity=float(orbit.ecc.value),
        inclination_deg=float(orbit.inc.to(u.deg).value),
        raan_deg=float(orbit.raan.to(u.deg).value),
        arg_periapsis_deg=float(orbit.argp.to(u.deg).value),
        perihelion_time=orbit.epoch.to_datetime(),
    )

    closest = ClosestApproach(
        datetime=closest_time,
        distance_km=distance_km,
        relative_speed_kms=rel_speed,
    )

    solution = OrbitSolution(
        semi_major_axis_au=orbit_data.semi_major_axis_au,
        eccentricity=orbit_data.eccentricity,
        inclination_deg=orbit_data.inclination_deg,
        raan_deg=orbit_data.raan_deg,
        arg_periapsis_deg=orbit_data.arg_periapsis_deg,
        perihelion_time=orbit_data.perihelion_time,
        closest_approach_time=closest.datetime,
        closest_distance_km=closest.distance_km,
        relative_speed_kms=closest.relative_speed_kms,
        source_observation_ids=",".join(str(obs.id) for obs in observations),
    )
    session.add(solution)
    session.commit()

    return ComputeResponse(
        orbit=orbit_data,
        closest_approach=closest,
        observation_ids=[obs.id for obs in observations],
    )


@app.post("/reset")
def reset_database(
    session: Session = Depends(get_session),
    current_user: User = Depends(get_current_user)
):
    """Удаляет все наблюдения и решения орбит из БД и очищает папку с загрузками.
    ВНИМАНИЕ: операция необратима.
    """
    # Удаляем строки из таблиц
    session.exec(delete(OrbitSolution))
    session.exec(delete(Observation))
    session.commit()

    # Очищаем папку uploads на хосте/в контейнере
    try:
        upload_dir = settings.upload_dir
        for child in upload_dir.iterdir():
            try:
                if child.is_file() or child.is_symlink():
                    child.unlink()
                elif child.is_dir():
                    # рекурсивно удалить директорию
                    import shutil as _sh

                    _sh.rmtree(child)
            except Exception as e:
                logger.warning("Failed to remove upload file %s: %s", child, e)
    except Exception as e:
        logger.exception("Failed to clean upload directory: %s", e)

    return {"status": "ok", "message": "Database and uploads cleared"}
