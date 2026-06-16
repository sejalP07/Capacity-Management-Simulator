from functools import lru_cache

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    database_url: str = "sqlite:///./capacity.db"
    redis_url: str = "redis://localhost:6379/0"
    jwt_secret: str = "dev-secret"
    jwt_algorithm: str = "HS256"
    access_token_expire_minutes: int = 1440
    google_client_id: str = ""
    google_client_secret: str = ""
    github_client_id: str = ""
    github_client_secret: str = ""
    oauth_redirect_base_url: str = "http://localhost:8000"
    frontend_url: str = "http://localhost:5173"

    model_config = SettingsConfigDict(env_file=".env", extra="ignore")


@lru_cache
def get_settings() -> Settings:
    return Settings()
