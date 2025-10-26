"""CRUD operations for database."""
from typing import List, Optional
from datetime import datetime
from sqlalchemy import select, delete
from sqlalchemy.ext.asyncio import AsyncSession

from app.models import Observation, User


# ========== User CRUD operations ==========

async def create_user(
    db: AsyncSession,
    username: str,
    email: str,
    hashed_password: str
) -> User:
    """Create a new user."""
    user = User(
        username=username,
        email=email,
        hashed_password=hashed_password
    )
    db.add(user)
    await db.flush()
    await db.refresh(user)
    return user


async def get_user_by_username(db: AsyncSession, username: str) -> Optional[User]:
    """Get user by username."""
    result = await db.execute(
        select(User).where(User.username == username)
    )
    return result.scalar_one_or_none()


async def get_user_by_email(db: AsyncSession, email: str) -> Optional[User]:
    """Get user by email."""
    result = await db.execute(
        select(User).where(User.email == email)
    )
    return result.scalar_one_or_none()


async def get_user_by_id(db: AsyncSession, user_id: int) -> Optional[User]:
    """Get user by ID."""
    result = await db.execute(
        select(User).where(User.id == user_id)
    )
    return result.scalar_one_or_none()


# ========== Observation CRUD operations ==========

async def create_observation(
    db: AsyncSession,
    ra_hours: float,
    dec_degrees: float,
    observation_time: datetime,
    photo_url: str
) -> Observation:
    """Create a new observation."""
    observation = Observation(
        ra_hours=ra_hours,
        dec_degrees=dec_degrees,
        observation_time=observation_time,
        photo_url=photo_url
    )
    db.add(observation)
    await db.flush()
    await db.refresh(observation)
    return observation


async def get_observations(db: AsyncSession) -> List[Observation]:
    """Get all observations ordered by observation time."""
    result = await db.execute(
        select(Observation).order_by(Observation.observation_time)
    )
    return list(result.scalars().all())


async def get_observation_by_id(db: AsyncSession, observation_id: int) -> Optional[Observation]:
    """Get a single observation by ID."""
    result = await db.execute(
        select(Observation).where(Observation.id == observation_id)
    )
    return result.scalar_one_or_none()


async def delete_observation(db: AsyncSession, observation_id: int) -> bool:
    """Delete an observation by ID. Returns True if deleted, False if not found."""
    observation = await get_observation_by_id(db, observation_id)
    if not observation:
        return False
    
    await db.delete(observation)
    await db.flush()
    return True
