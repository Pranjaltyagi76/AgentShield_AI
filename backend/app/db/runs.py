from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import Mapped, mapped_column

from app.db.models import Base


class Run(Base):
    __tablename__ = "test_runs"
    __table_args__ = (UniqueConstraint("owner_id", "request_key"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True
    )
    version_id: Mapped[UUID] = mapped_column(ForeignKey("agent_versions.id", ondelete="CASCADE"))
    request_key: Mapped[str]
    request_hash: Mapped[str]
    config: Mapped[dict] = mapped_column(JSONB)
    status: Mapped[str] = mapped_column(index=True)
    queued_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    queue_expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True))
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    finished_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    heartbeat_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    worker_id: Mapped[UUID | None]
    cancel_requested: Mapped[bool] = mapped_column(default=False)
    reason: Mapped[str | None]
    trace_bytes: Mapped[int] = mapped_column(default=0)
    budget_used: Mapped[int] = mapped_column(default=0)


class Result(Base):
    __tablename__ = "scenario_results"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    run_id: Mapped[UUID] = mapped_column(ForeignKey("test_runs.id", ondelete="CASCADE"), index=True)
    position: Mapped[int]
    scenario_id: Mapped[str]
    scenario_version: Mapped[int]
    status: Mapped[str]
    reason: Mapped[str | None]
    outcome: Mapped[str | None]
    steps: Mapped[int] = mapped_column(default=0)
    next_sequence: Mapped[int] = mapped_column(default=1)
    started_at: Mapped[datetime | None] = mapped_column(DateTime(timezone=True))
    last_observation: Mapped[dict | None] = mapped_column(JSONB)


class Event(Base):
    __tablename__ = "trace_events"
    __table_args__ = (UniqueConstraint("result_id", "sequence"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    result_id: Mapped[UUID] = mapped_column(ForeignKey("scenario_results.id", ondelete="CASCADE"))
    sequence: Mapped[int]
    kind: Mapped[str]
    payload: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
