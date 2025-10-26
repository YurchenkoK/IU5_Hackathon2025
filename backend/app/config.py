"""Application configuration."""
import os
from pathlib import Path
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Base directory
BASE_DIR = Path(__file__).resolve().parent.parent

# Database configuration
DATABASE_URL = os.getenv(
    "DATABASE_URL",
    "postgresql+asyncpg://postgres:postgres@localhost:5432/comet_db"
)

# Upload directory
UPLOAD_DIR = BASE_DIR / "uploads"
UPLOAD_DIR.mkdir(exist_ok=True)

# CORS settings
CORS_ORIGINS = [
    "http://localhost",
    "http://localhost:80",
    "http://localhost:3000",
    "http://localhost:5173",
    "http://localhost:8080",
    "http://frontend:80",
]

# File upload settings
MAX_UPLOAD_SIZE = 10 * 1024 * 1024  # 10 MB
ALLOWED_EXTENSIONS = {".jpg", ".jpeg", ".png", ".gif", ".bmp", ".webp"}
