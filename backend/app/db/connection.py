"""Lazy, small PostgreSQL pool with bounded connection and query timeouts."""

from typing import Literal, Protocol

from sqlalchemy import create_engine, text
from sqlalchemy.engine import make_url

from app.core.settings import Settings

DatabaseStatus = Literal["connected", "unavailable", "not_configured"]


class DatabaseProbe(Protocol):
    def check(self) -> DatabaseStatus: ...

    def close(self) -> None: ...


class Database:
    def __init__(self, settings: Settings) -> None:
        self.engine = None
        if settings.database_url:
            url = make_url(settings.database_url.get_secret_value()).set(
                drivername="postgresql+psycopg"
            )
            self.engine = create_engine(
                url,
                pool_size=2,
                max_overflow=0,
                pool_timeout=2,
                pool_pre_ping=True,
                pool_recycle=300,
                hide_parameters=True,
                connect_args={"connect_timeout": 3, "prepare_threshold": None},
            )

    def check(self) -> DatabaseStatus:
        if self.engine is None:
            return "not_configured"
        with self.engine.connect() as connection:
            connection.execute(text("SET LOCAL statement_timeout = '3000ms'"))
            revision = connection.scalar(text("SELECT version_num FROM alembic_version"))
            if revision != "0004":
                return "unavailable"
        return "connected"

    def close(self) -> None:
        if self.engine:
            self.engine.dispose()
