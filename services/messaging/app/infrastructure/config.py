from functools import lru_cache

from pydantic_settings import BaseSettings


def normalize_database_url(database_url: str) -> str:
    if database_url.startswith("postgres://"):
        return database_url.replace("postgres://", "postgresql+asyncpg://", 1)
    if database_url.startswith("postgresql://"):
        return database_url.replace("postgresql://", "postgresql+asyncpg://", 1)
    return database_url


class DatabaseSettings(BaseSettings):
    DATABASE_URL: str = "sqlite+aiosqlite:///./messaging.db"
    LOG_LEVEL: str = "INFO"

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}

    @property
    def sqlalchemy_database_url(self) -> str:
        return normalize_database_url(self.DATABASE_URL)


class Settings(BaseSettings):
    WEBHOOK_VERIFY_TOKEN: str
    APP_SECRET: str
    DATABASE_URL: str = "sqlite+aiosqlite:///./messaging.db"
    LOG_LEVEL: str = "INFO"
    OLLAMA_BASE_URL: str
    OLLAMA_MODEL: str
    OLLAMA_PROMPT_VERSION: str
    WHISPER_BASE_URL: str = ""
    WHISPER_API_KEY: str = ""
    WHATSAPP_ACCESS_TOKEN: str = ""
    CORS_ORIGINS: list[str] = ["*"]

    model_config = {"env_file": ".env", "env_file_encoding": "utf-8", "extra": "ignore"}


@lru_cache()
def get_settings() -> Settings:
    return Settings()


@lru_cache()
def get_database_settings() -> DatabaseSettings:
    return DatabaseSettings()
