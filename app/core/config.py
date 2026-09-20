"""Настройки приложения через pydantic-settings."""

from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    model_config = SettingsConfigDict(env_file=".env", extra="ignore")

    max_function_lines: int = 50
    min_weight: float = 0.1
    max_weight: float = 2.0
    upvote_step: float = 0.1
    downvote_step: float = 0.2
    app_host: str = "0.0.0.0"
    app_port: int = 8000


_settings: Settings | None = None


def get_settings() -> Settings:
    global _settings
    if _settings is None:
        _settings = Settings()
    return _settings
