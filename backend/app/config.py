from pathlib import Path

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    database_url: str = "postgresql://cometuser:cometpass123@localhost:5432/cometlab"
    upload_dir: Path = Path("uploads")
    frontend_origin: str = "http://localhost:5173"
    sample_propagation_days: int = 365

    class Config:
        env_file = ".env"
        env_file_encoding = "utf-8"


settings = Settings()
settings.upload_dir.mkdir(parents=True, exist_ok=True)
