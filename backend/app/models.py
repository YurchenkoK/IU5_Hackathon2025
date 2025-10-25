from datetime import datetime
from typing import Optional

from sqlmodel import Field, SQLModel


class Observation(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    ra_hours: float
    dec_degrees: float
    observation_time: datetime
    photo_path: str
    created_at: datetime = Field(default_factory=datetime.utcnow)


class OrbitSolution(SQLModel, table=True):
    id: Optional[int] = Field(default=None, primary_key=True)
    semi_major_axis_au: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    arg_periapsis_deg: float
    perihelion_time: datetime
    closest_approach_time: datetime
    closest_distance_km: float
    relative_speed_kms: float
    source_observation_ids: str
    created_at: datetime = Field(default_factory=datetime.utcnow)
