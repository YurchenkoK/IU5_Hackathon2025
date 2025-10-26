"""Main FastAPI application."""
import uuid
from pathlib import Path
from datetime import datetime
from typing import List

from fastapi import FastAPI, UploadFile, File, Form, Depends, HTTPException, status
from fastapi.middleware.cors import CORSMiddleware
from fastapi.staticfiles import StaticFiles
from fastapi.responses import JSONResponse
from sqlalchemy.ext.asyncio import AsyncSession

from app.config import CORS_ORIGINS, UPLOAD_DIR, MAX_UPLOAD_SIZE, ALLOWED_EXTENSIONS
from app.database import get_db, init_db
from app import crud
from app.schemas import (
    ObservationResponse, ComputeResponse,
    UserCreate, UserLogin, UserResponse, Token
)
from app.orbit_calc import compute_orbit_from_observations
from app.auth import hash_password, verify_password, create_access_token, get_current_active_user

# Create FastAPI app
app = FastAPI(
    title="Comet Observation API",
    description="Backend для отслеживания комет и расчета орбит",
    version="1.0.0"
)

# Add CORS middleware
app.add_middleware(
    CORSMiddleware,
    allow_origins=CORS_ORIGINS,
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

# Mount uploads directory for static file serving
app.mount("/uploads", StaticFiles(directory=str(UPLOAD_DIR)), name="uploads")


@app.on_event("startup")
async def startup_event():
    """Initialize database on startup."""
    await init_db()
    print("Database initialized successfully")


@app.get("/", tags=["Health"])
async def root():
    """Health check endpoint."""
    return {"status": "ok", "message": "Comet Observation API"}


# ========== Authentication Routes ==========

@app.post("/register", response_model=UserResponse, status_code=status.HTTP_201_CREATED, tags=["Auth"])
async def register(user_data: UserCreate, db: AsyncSession = Depends(get_db)):
    """Register a new user."""
    # Check if username already exists
    existing_user = await crud.get_user_by_username(db, user_data.username)
    if existing_user:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Username already registered"
        )
    
    # Check if email already exists
    existing_email = await crud.get_user_by_email(db, user_data.email)
    if existing_email:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Email already registered"
        )
    
    # Create new user
    hashed_pw = hash_password(user_data.password)
    user = await crud.create_user(
        db=db,
        username=user_data.username,
        email=user_data.email,
        hashed_password=hashed_pw
    )
    await db.commit()
    
    return user


@app.post("/login", response_model=Token, tags=["Auth"])
async def login(user_data: UserLogin, db: AsyncSession = Depends(get_db)):
    """Login and get access token."""
    # Find user
    user = await crud.get_user_by_username(db, user_data.username)
    if not user or not verify_password(user_data.password, user.hashed_password):
        raise HTTPException(
            status_code=status.HTTP_401_UNAUTHORIZED,
            detail="Incorrect username or password",
            headers={"WWW-Authenticate": "Bearer"},
        )
    
    if not user.is_active:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Inactive user"
        )
    
    # Create access token
    access_token = create_access_token(data={"sub": user.username})
    return {"access_token": access_token, "token_type": "bearer"}


@app.get("/me", response_model=UserResponse, tags=["Auth"])
async def get_current_user_info(current_user = Depends(get_current_active_user)):
    """Get current user information."""
    return current_user


# ========== Observation Routes ==========

@app.get("/observations", response_model=List[ObservationResponse], tags=["Observations"])
async def get_observations(db: AsyncSession = Depends(get_db)):
    """Get all observations."""
    observations = await crud.get_observations(db)
    return observations


@app.post("/observations", response_model=ObservationResponse, status_code=status.HTTP_201_CREATED, tags=["Observations"])
async def create_observation(
    ra_hours: float = Form(..., description="Right Ascension in hours (0-24)"),
    dec_degrees: float = Form(..., description="Declination in degrees (-90 to 90)"),
    observation_time: str = Form(..., description="Observation time in ISO format"),
    photo: UploadFile = File(..., description="Photo of observation"),
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Create a new observation with photo upload. Requires authentication."""
    # Validate RA and Dec
    if not (0 <= ra_hours < 24):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="RA must be between 0 and 24 hours"
        )
    
    if not (-90 <= dec_degrees <= 90):
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Dec must be between -90 and 90 degrees"
        )
    
    # Parse observation time
    try:
        obs_time = datetime.fromisoformat(observation_time.replace('Z', '+00:00'))
    except ValueError:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail="Invalid observation_time format. Use ISO 8601 format."
        )
    
    # Validate file size
    contents = await photo.read()
    if len(contents) > MAX_UPLOAD_SIZE:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File size exceeds maximum allowed size of {MAX_UPLOAD_SIZE / 1024 / 1024}MB"
        )
    
    # Validate file extension
    file_ext = Path(photo.filename or "").suffix.lower()
    if file_ext not in ALLOWED_EXTENSIONS:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"File type not allowed. Allowed types: {', '.join(ALLOWED_EXTENSIONS)}"
        )
    
    # Generate unique filename
    unique_filename = f"{uuid.uuid4()}{file_ext}"
    file_path = UPLOAD_DIR / unique_filename
    
    # Save file
    with open(file_path, "wb") as f:
        f.write(contents)
    
    # Create observation in database
    photo_url = f"/uploads/{unique_filename}"
    observation = await crud.create_observation(
        db=db,
        ra_hours=ra_hours,
        dec_degrees=dec_degrees,
        observation_time=obs_time,
        photo_url=photo_url
    )
    
    return observation


@app.delete("/observations/{observation_id}", status_code=status.HTTP_204_NO_CONTENT, tags=["Observations"])
async def delete_observation(
    observation_id: int,
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """Delete an observation by ID. Requires authentication."""
    deleted = await crud.delete_observation(db, observation_id)
    if not deleted:
        raise HTTPException(
            status_code=status.HTTP_404_NOT_FOUND,
            detail=f"Observation with id {observation_id} not found"
        )
    return None


@app.post("/compute", response_model=ComputeResponse, tags=["Orbit"])
async def compute_orbit(
    db: AsyncSession = Depends(get_db),
    current_user = Depends(get_current_active_user)
):
    """
    Compute comet orbit and closest approach to Earth.
    Requires at least 5 observations. Requires authentication.
    """
    observations = await crud.get_observations(db)
    
    if len(observations) < 5:
        raise HTTPException(
            status_code=status.HTTP_400_BAD_REQUEST,
            detail=f"Need at least 5 observations, got {len(observations)}"
        )
    
    try:
        # Compute orbit and closest approach
        result = compute_orbit_from_observations(observations)
        return result
    except Exception as e:
        raise HTTPException(
            status_code=status.HTTP_500_INTERNAL_SERVER_ERROR,
            detail=f"Failed to compute orbit: {str(e)}"
        )


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=8000)
