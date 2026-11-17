"""Validated configuration for opt-in scripted execution."""

from pathlib import Path
from typing import Literal
from urllib.parse import urlsplit

from pydantic import Field, SecretStr, field_validator, model_validator
from pydantic_settings import BaseSettings, SettingsConfigDict
from sqlalchemy.engine import make_url
from sqlalchemy.exc import ArgumentError

ROOT = Path(__file__).resolve().parents[3]


class Settings(BaseSettings):
    model_config = SettingsConfigDict(
        env_file=(ROOT / ".env", ROOT / "backend" / ".env"),
        env_file_encoding="utf-8",
        extra="ignore",
        hide_input_in_errors=True,
    )

    app_env: Literal["development", "test", "production"] = "development"
    database_url: SecretStr | None = None
    cors_origins: list[str] = Field(
        default_factory=lambda: ["http://localhost:5173", "http://127.0.0.1:5173"]
    )
    log_level: Literal["DEBUG", "INFO", "WARNING", "ERROR"] = "INFO"
    public_runs_enabled: bool = False
    public_llm_enabled: Literal[False] = False
    local_runs_enabled: bool = False
    max_database_bytes: int = Field(default=524288000, gt=0, le=524288000)

    @model_validator(mode="after")
    def local_runtime(self):
        if self.local_runs_enabled and (
            self.app_env == "production"
            or not self.database_url
            or make_url(self.database_url.get_secret_value()).host
            not in {"localhost", "127.0.0.1", "::1"}
        ):
            raise ValueError("Local execution requires development/test and loopback PostgreSQL")
        if self.public_runs_enabled and (
            self.local_runs_enabled
            or self.app_env != "production"
            or not self.database_url
            or not self.cors_origins
            or any(not origin.startswith("https://") for origin in self.cors_origins)
        ):
            raise ValueError(
                "Public demo requires production, a configured database and explicit HTTPS origins"
            )
        return self

    llm_provider: Literal["demo"] = "demo"

    @field_validator("public_llm_enabled", mode="before")
    @classmethod
    def parse_disabled_environment_flag(cls, value: object) -> object:
        # Environment values are strings; Literal[False] does not coerce them.
        # Only explicit false spellings are normalized. True/unknown values
        # still fail the Literal validation and cannot enable Phase 0 execution.
        if isinstance(value, str) and value.strip().lower() in {"false", "0", "off", "no"}:
            return False
        return value

    @field_validator("database_url")
    @classmethod
    def validate_database_url(cls, value: SecretStr | None) -> SecretStr | None:
        if value is None:
            return None
        try:
            url = make_url(value.get_secret_value())
            valid = (
                url.drivername in {"postgres", "postgresql", "postgresql+psycopg"}
                and url.host
                and url.database
                and url.username
            )
        except (ArgumentError, ValueError):
            valid = False
        if not valid:
            raise ValueError("DATABASE_URL must be a PostgreSQL URL with host, user, and database")
        return value

    @field_validator("cors_origins")
    @classmethod
    def validate_origins(cls, origins: list[str]) -> list[str]:
        for origin in origins:
            parsed = urlsplit(origin)
            if (
                parsed.scheme not in {"http", "https"}
                or not parsed.netloc
                or parsed.username
                or parsed.password
                or parsed.path
                or parsed.query
                or parsed.fragment
                or "*" in origin
            ):
                raise ValueError("CORS_ORIGINS must contain explicit HTTP(S) origins without paths")
        return list(dict.fromkeys(origins))
