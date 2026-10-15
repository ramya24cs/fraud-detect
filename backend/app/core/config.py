
import math
from pathlib import Path
from typing import Any

from pydantic import field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict


class Settings(BaseSettings):
    DATABASE_URL: str
    NEON_DIRECT_URL: str | None = None
    JWT_SECRET_KEY: str = "local-dev-secret-key-change-me"
    JWT_ALGORITHM: str = "HS256"
    JWT_EXPIRE_MINUTES: int = 60
    MODEL_DIR: str = "./ml/models"
    CORS_ORIGINS: str = "http://localhost:5173"
    RISK_LOW_THRESHOLD: float = 0.30
    RISK_HIGH_THRESHOLD: float = 0.70
    SMTP_HOST: str | None = "smtp.gmail.com"
    SMTP_PORT: int = 587
    SMTP_USERNAME: str | None = None
    SMTP_PASSWORD: str | None = None
    SMTP_FROM_EMAIL: str | None = None
    SMTP_USE_STARTTLS: bool = True
    FRONTEND_BASE_URL: str = "http://localhost:5173"

    model_config = SettingsConfigDict(
        env_file=".env",
        env_file_encoding="utf-8",
        extra="ignore",
    )

    @field_validator("DATABASE_URL", "NEON_DIRECT_URL", mode="before")
    @classmethod
    def _normalize_database_url(cls, value, info):
        if value is None or not str(value).strip():
            if info.field_name == "NEON_DIRECT_URL":
                return None
            raise ValueError(
                "DATABASE_URL must point to the configured PostgreSQL database."
            )
        url = str(value).strip()
        if url.startswith("postgres://"):
            return "postgresql+psycopg://" + url[len("postgres://") :]
        if url.startswith("postgresql://"):
            return "postgresql+psycopg://" + url[len("postgresql://") :]
        if url.startswith("postgresql+psycopg2://"):
            return "postgresql+psycopg://" + url[
                len("postgresql+psycopg2://") :
            ]
        return url

    @field_validator("JWT_SECRET_KEY", mode="before")
    @classmethod
    def _coalesce_empty_strings(cls, value):
        if value is None:
            return "local-dev-secret-key-change-me"
        if isinstance(value, str) and not value.strip():
            return "local-dev-secret-key-change-me"
        return value

    @field_validator("RISK_LOW_THRESHOLD", "RISK_HIGH_THRESHOLD")
    @classmethod
    def _validate_risk_thresholds(cls, value: float, info) -> float:
        value = float(value)
        if not math.isfinite(value) or not 0.0 <= value <= 1.0:
            raise ValueError(
                f"{info.field_name} must be between 0.0 and 1.0"
            )
        return value

    @model_validator(mode="after")
    def _validate_threshold_order(self):
        if self.RISK_LOW_THRESHOLD >= self.RISK_HIGH_THRESHOLD:
            raise ValueError(
                "RISK_LOW_THRESHOLD must be lower than RISK_HIGH_THRESHOLD"
            )
        return self


settings = Settings()
_SETTINGS_ENV_FILE = Path(settings.model_config["env_file"])


def get_current_settings() -> Settings:
    global _SETTINGS_ENV_FILE_MTIME_NS

    try:
        env_file_mtime_ns = _SETTINGS_ENV_FILE.stat().st_mtime_ns
    except OSError:
        return settings

    if env_file_mtime_ns != _SETTINGS_ENV_FILE_MTIME_NS:
        refreshed_settings = Settings(_env_file=_SETTINGS_ENV_FILE)
        _SETTINGS_ENV_FILE_MTIME_NS = env_file_mtime_ns
        return refreshed_settings
    return settings


try:
    _SETTINGS_ENV_FILE_MTIME_NS = _SETTINGS_ENV_FILE.stat().st_mtime_ns
except OSError:
    _SETTINGS_ENV_FILE_MTIME_NS = None
