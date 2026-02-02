from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    project_id: str = "biu-dorm-exchange"
    google_application_credentials: str | None = None
    environment: str = "development"
    cors_origins: list[str] = ["http://localhost:3000"]
    match_expiry_hours: int = 48
    listing_expiry_days: int = 30

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache
def get_settings() -> Settings:
    return Settings()
