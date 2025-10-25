from datetime import datetime
from typing import List

from pydantic import BaseModel


class ObservationRead(BaseModel):
    id: int
    ra_hours: float
    dec_degrees: float
    observation_time: datetime
    photo_url: str


class OrbitElements(BaseModel):
    semi_major_axis_au: float
    eccentricity: float
    inclination_deg: float
    raan_deg: float
    arg_periapsis_deg: float
    perihelion_time: datetime


class ClosestApproach(BaseModel):
    datetime: datetime
    distance_km: float
    relative_speed_kms: float


class ComputeResponse(BaseModel):
    orbit: OrbitElements
    closest_approach: ClosestApproach
    observation_ids: List[int]
