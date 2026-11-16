"""Relational schema for temporary workspaces and the curated catalog."""

from datetime import datetime
from uuid import UUID, uuid4

from sqlalchemy import CheckConstraint, DateTime, ForeignKey, UniqueConstraint, func
from sqlalchemy.dialects.postgresql import JSONB
from sqlalchemy.orm import DeclarativeBase, Mapped, mapped_column


class Base(DeclarativeBase):
    pass


class Guest(Base):
    __tablename__ = "guest_sessions"
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    credential_hash: Mapped[str] = mapped_column(unique=True)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    expires_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), index=True)


class Agent(Base):
    __tablename__ = "agents"
    __table_args__ = (CheckConstraint("is_shared = (owner_id IS NULL)"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    owner_id: Mapped[UUID | None] = mapped_column(
        ForeignKey("guest_sessions.id", ondelete="CASCADE"), index=True
    )
    is_shared: Mapped[bool] = mapped_column(default=False)
    name: Mapped[str]
    description: Mapped[str]
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())
    updated_at: Mapped[datetime] = mapped_column(
        DateTime(timezone=True), server_default=func.now(), onupdate=func.now()
    )


class Version(Base):
    __tablename__ = "agent_versions"
    __table_args__ = (UniqueConstraint("agent_id", "version_number"),)
    id: Mapped[UUID] = mapped_column(primary_key=True, default=uuid4)
    agent_id: Mapped[UUID] = mapped_column(ForeignKey("agents.id", ondelete="CASCADE"))
    version_number: Mapped[int]
    provider: Mapped[str]
    model_name: Mapped[str]
    demo_profile: Mapped[str]
    behavior_version: Mapped[str]
    system_prompt: Mapped[str]
    prompt_hash: Mapped[str]
    tool_config_json: Mapped[list] = mapped_column(JSONB)
    policy_config_json: Mapped[dict] = mapped_column(JSONB)
    created_at: Mapped[datetime] = mapped_column(DateTime(timezone=True), server_default=func.now())


class Scenario(Base):
    __tablename__ = "scenarios"
    id: Mapped[str] = mapped_column(primary_key=True)
    name: Mapped[str]
    category: Mapped[str]
    severity: Mapped[str]


class ScenarioVersion(Base):
    __tablename__ = "scenario_versions"
    scenario_id: Mapped[str] = mapped_column(ForeignKey("scenarios.id"), primary_key=True)
    version: Mapped[int] = mapped_column(primary_key=True)
    description: Mapped[str]
    runtime_context: Mapped[dict] = mapped_column(JSONB)
    evaluator_rule: Mapped[str]
