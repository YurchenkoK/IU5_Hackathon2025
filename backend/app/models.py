"""Database models."""
from datetime import datetime
from sqlalchemy import Column, Integer, Float, String, DateTime, Boolean
from sqlalchemy.ext.declarative import declarative_base

Base = declarative_base()


class User(Base):
    """User model for authentication."""
    
    __tablename__ = "users"

    id = Column(Integer, primary_key=True, index=True)
    username = Column(String(50), unique=True, nullable=False, index=True)
    email = Column(String(100), unique=True, nullable=False, index=True)
    hashed_password = Column(String(255), nullable=False)
    is_active = Column(Boolean, default=True, nullable=False)
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<User(id={self.id}, username={self.username}, email={self.email})>"


class Observation(Base):
    """Observation model for storing comet observation data."""
    
    __tablename__ = "observations"

    id = Column(Integer, primary_key=True, index=True)
    ra_hours = Column(Float, nullable=False)  # Right Ascension in hours (0-24)
    dec_degrees = Column(Float, nullable=False)  # Declination in degrees (-90 to 90)
    observation_time = Column(DateTime(timezone=True), nullable=False)  # UTC timestamp
    photo_url = Column(String(255), nullable=False)  # Path to uploaded photo
    created_at = Column(DateTime(timezone=True), default=datetime.utcnow, nullable=False)

    def __repr__(self):
        return f"<Observation(id={self.id}, ra={self.ra_hours}, dec={self.dec_degrees}, time={self.observation_time})>"
