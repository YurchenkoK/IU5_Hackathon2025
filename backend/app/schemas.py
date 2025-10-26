"""Pydantic schemas for request/response validation."""
from datetime import datetime
from typing import List, Optional
from pydantic import BaseModel, Field, EmailStr


# ========== User Schemas ==========

class UserCreate(BaseModel):
    """Schema for user registration."""
    username: str = Field(..., min_length=3, max_length=50, description="Unique username")
    email: EmailStr = Field(..., description="User email address")
    password: str = Field(..., min_length=6, description="User password")


class UserLogin(BaseModel):
    """Schema for user login."""
    username: str = Field(..., description="Username")
    password: str = Field(..., description="Password")


class UserResponse(BaseModel):
    """Schema for user response."""
    id: int
    username: str
    email: str
    is_active: bool
    created_at: datetime

    class Config:
        from_attributes = True


class Token(BaseModel):
    """Schema for JWT token response."""
    access_token: str
    token_type: str = "bearer"


class TokenData(BaseModel):
    """Schema for token payload data."""
    username: Optional[str] = None


# ========== Observation Schemas ==========

class ObservationCreate(BaseModel):
    """Schema for creating a new observation."""
    ra_hours: float = Field(..., ge=0, lt=24, description="Right Ascension in hours (0-24)")
    dec_degrees: float = Field(..., ge=-90, le=90, description="Declination in degrees (-90 to 90)")
    observation_time: datetime = Field(..., description="UTC timestamp of observation")


class ObservationResponse(BaseModel):
    """Schema for observation response."""
    id: int
    ra_hours: float
    dec_degrees: float
    observation_time: datetime
    photo_url: str
    created_at: datetime

    class Config:
        from_attributes = True


class OrbitElements(BaseModel):
    """Orbital elements of the comet."""
    semi_major_axis_au: float = Field(..., description="Большая полуось орбиты (а.е.) - средний радиус орбиты")
    eccentricity: float = Field(..., description="Эксцентриситет (e) - степень вытянутости орбиты (0 = круг, 1 = парабола)")
    inclination_deg: float = Field(..., description="Наклонение орбиты (i) - угол между плоскостью орбиты и эклиптикой")
    raan_deg: float = Field(..., description="Долгота восходящего узла (Ω) - угол от точки весеннего равноденствия до восходящего узла")
    arg_periapsis_deg: float = Field(..., description="Аргумент перигелия (ω) - угол от узла до ближайшей точки к Солнцу")
    perihelion_time: datetime = Field(..., description="Время прохождения перигелия (T_peri) - момент максимального приближения к Солнцу")


class ClosestApproach(BaseModel):
    """Details of closest approach to Earth."""
    approach_datetime: datetime = Field(..., description="Дата и время максимального сближения с Землей")
    distance_km: float = Field(..., description="Минимальное расстояние до Земли (км)")
    relative_speed_kms: float = Field(..., description="Относительная скорость сближения (км/с)")


class ComputeResponse(BaseModel):
    """Response from orbit computation."""
    orbit: OrbitElements
    closest_approach: ClosestApproach
    observation_ids: List[int] = Field(..., description="IDs of observations used")
