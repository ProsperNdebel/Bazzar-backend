from functools import lru_cache
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    # Dev default is SQLite (zero setup). Production overrides this via the
    # DATABASE_URL env var with a Postgres URL (postgresql+asyncpg://...).
    database_url: str = "sqlite+aiosqlite:///./bazaar.db"

    jwt_secret: str = "change-me-in-production"
    jwt_algorithm: str = "HS256"
    access_token_ttl_minutes: int = 60 * 24 * 7  # 7 days

    tax_rate: float = 0.095  # matches the 9.5% used in the app's CartScreen


@lru_cache
def get_settings() -> Settings:
    return Settings()
