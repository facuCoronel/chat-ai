from functools import lru_cache

from pydantic_settings import BaseSettings


class Settings(BaseSettings):
    WEBHOOK_VERIFY_TOKEN: str
    APP_SECRET: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./messaging.db"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()
