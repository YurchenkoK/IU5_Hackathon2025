from datetime import datetime
from pathlib import Path
from typing import List
from uuid import uuid4
import shutil
import logging

import astropy.units as u
from fastapi import Depends, FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from sqlmodel import Session, select
from sqlmodel import delete
from fastapi.security import OAuth2PasswordRequestForm

# Логгер для модуля
logger = logging.getLogger(__name__)

from .config import settings
from .database import get_session, init_db
from .models import Observation, OrbitSolution
from .orbit import derive_orbit, find_closest_approach
from .schemas import ClosestApproach, ComputeResponse, ObservationRead, OrbitElements
from .auth import authenticate_client, create_access_token, get_current_client

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
def list_observations(session: Session = Depends(get_session)):
    observations = session.exec(select(Observation).order_by(Observation.observation_time)).all()
    return [_to_read(obs) for obs in observations]


@app.delete("/observations/{obs_id}", status_code=204)
def delete_observation(obs_id: int, session: Session = Depends(get_session)):
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
def compute_orbit(session: Session = Depends(get_session), username: str = Depends(get_current_client)):
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
def reset_database(session: Session = Depends(get_session), username: str = Depends(get_current_client)):
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


@app.post('/login')
def login(form_data: OAuth2PasswordRequestForm = Depends()):
    if not authenticate_client(form_data.username, form_data.password):
        raise HTTPException(status_code=400, detail='Incorrect username or password')
    access_token = create_access_token(data={"sub": form_data.username})
    return {"access_token": access_token, "token_type": "bearer"}
