"""Guest registry and read-only catalog. Ownership is resolved inside each transaction."""

import secrets
from collections import deque
from datetime import UTC, datetime, timedelta
from hashlib import sha256
from threading import Lock
from time import monotonic
from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from pydantic import BaseModel, ConfigDict, Field, field_validator
from sqlalchemy import delete, func, or_, select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Agent, Guest, Scenario, ScenarioVersion, Version
from app.suite import MEMBERS, SUITE

router = APIRouter(prefix="/api/v1")
MAX_GUESTS, MAX_AGENTS, MAX_VERSIONS = 128, 8, 4


class IssueLimiter:
    def __init__(self):
        self.events = deque()
        self.lock = Lock()

    def admit(self, peer):
        with self.lock:
            now = monotonic()
            while self.events and self.events[0][0] <= now - 600:
                self.events.popleft()
            if len(self.events) >= 60 or sum(p == peer for _, p in self.events) >= 8:
                raise HTTPException(429, headers={"Retry-After": "600"})
            self.events.append((now, peer))


def db(request: Request):
    engine = getattr(request.app.state.database, "engine", None)
    if engine is None:
        raise HTTPException(503)
    try:
        with Session(engine) as session, session.begin():
            yield session
    except SQLAlchemyError:
        raise HTTPException(503) from None


DB = Annotated[Session, Depends(db, scope="function")]


def digest(value: str):
    return sha256(value.encode()).hexdigest()


def guest(request, session, required=True):
    auth = request.headers.get("authorization")
    if not auth and not required:
        return None
    scheme, _, token = (auth or "").partition(" ")
    if scheme.lower() != "bearer" or len(token) != 43:
        raise HTTPException(401)
    row = session.scalar(
        select(Guest)
        .where(Guest.credential_hash == digest(token), Guest.expires_at > func.clock_timestamp())
        .with_for_update(key_share=True)
    )
    if not row:
        raise HTTPException(401)
    return row


def cleanup(engine):
    with Session(engine) as s, s.begin():
        ids = (
            select(Guest.id)
            .where(Guest.expires_at <= func.now())
            .order_by(Guest.expires_at)
            .limit(16)
            .with_for_update(skip_locked=True)
        )
        s.execute(
            delete(Guest).where(Guest.id.in_(ids)).execution_options(synchronize_session=False)
        )


def limits():
    return {"profiles": MAX_AGENTS, "versions_per_profile": MAX_VERSIONS}


@router.post("/guest-sessions", status_code=201)
def issue(request: Request, s: DB):
    request.app.state.issue_limiter.admit(request.client.host if request.client else "unknown")
    s.execute(text("SELECT pg_advisory_xact_lock(19485121)"))
    if s.scalar(select(func.count()).select_from(Guest)) >= MAX_GUESTS:
        raise HTTPException(503)
    token = secrets.token_urlsafe(32)
    expiry = datetime.now(UTC) + timedelta(days=7)
    s.add(Guest(credential_hash=digest(token), expires_at=expiry))
    return {"credential": token, "expires_at": expiry, "limits": limits()}


@router.get("/guest-session")
def inspect(request: Request, s: DB):
    return {"expires_at": guest(request, s).expires_at, "limits": limits()}


@router.delete("/guest-session", status_code=204)
def revoke(request: Request, s: DB):
    s.delete(guest(request, s))
    return Response(status_code=204)


class Strict(BaseModel):
    model_config = ConfigDict(extra="forbid", str_strip_whitespace=True)


class Metadata(Strict):
    name: str = Field(min_length=1, max_length=80)
    description: str = Field(default="", max_length=512)


class MetadataPatch(Strict):
    name: str | None = Field(default=None, min_length=1, max_length=80)
    description: str | None = Field(default=None, max_length=512)

    @field_validator("name", "description")
    @classmethod
    def reject_null(cls, value):
        if value is None:
            raise ValueError("Expected text")
        return value


class Configuration(Strict):
    demo_profile: Literal["hardened", "vulnerable"] = "hardened"
    system_prompt: str = Field(
        default="Use synthetic workspace records only.", min_length=1, max_length=16384
    )
    allowed_tools: list[
        Literal[
            "search_docs", "get_customer_record", "send_message_simulated", "export_file_simulated"
        ]
    ] = Field(default_factory=list, max_length=4)
    require_confirmation: Literal[True] = True

    @field_validator("system_prompt")
    @classmethod
    def size(cls, v):
        if len(v.encode()) > 16384:
            raise ValueError("Prompt exceeds byte limit")
        return v


class NewAgent(Metadata):
    configuration: Configuration = Field(default_factory=Configuration)


def summary(a):
    return {"id": a.id, "name": a.name, "description": a.description, "is_shared": a.is_shared}


def version_view(v):
    return {
        k: getattr(v, k)
        for k in (
            "id",
            "version_number",
            "provider",
            "model_name",
            "demo_profile",
            "behavior_version",
            "system_prompt",
            "prompt_hash",
            "tool_config_json",
            "policy_config_json",
            "created_at",
        )
    }


def accessible(s, g, aid, write=False):
    scope = Agent.is_shared if g is None else or_(Agent.is_shared, Agent.owner_id == g.id)
    a = s.scalar(select(Agent).where(Agent.id == aid, scope))
    if a is None:
        raise HTTPException(404)
    if write and a.is_shared:
        raise HTTPException(403)
    return a


def append(s, a, c):
    n = 1 + (
        s.scalar(select(func.max(Version.version_number)).where(Version.agent_id == a.id)) or 0
    )
    if n > MAX_VERSIONS:
        raise HTTPException(409)
    v = Version(
        agent_id=a.id,
        version_number=n,
        provider="demo",
        model_name="scripted",
        demo_profile=c.demo_profile,
        behavior_version="2",
        system_prompt=c.system_prompt,
        prompt_hash=digest(c.system_prompt),
        tool_config_json=c.allowed_tools,
        policy_config_json={"require_confirmation": True},
    )
    s.add(v)
    s.flush()
    return version_view(v)


@router.get("/agents")
def agents(request: Request, s: DB):
    g = guest(request, s, False)
    scope = Agent.is_shared if g is None else or_(Agent.is_shared, Agent.owner_id == g.id)
    return [
        summary(a)
        for a in s.scalars(select(Agent).where(scope).order_by(Agent.created_at, Agent.id))
    ]


@router.post("/agents", status_code=201)
def create(data: NewAgent, request: Request, s: DB):
    g = guest(request, s)
    if (
        s.scalar(select(func.count()).select_from(Agent).where(Agent.owner_id == g.id))
        >= MAX_AGENTS
    ):
        raise HTTPException(409)
    a = Agent(owner_id=g.id, name=data.name, description=data.description)
    s.add(a)
    s.flush()
    return {**summary(a), "versions": [append(s, a, data.configuration)]}


@router.get("/agents/{aid}")
def detail(aid: UUID, request: Request, s: DB):
    a = accessible(s, guest(request, s, False), aid)
    versions = s.scalars(
        select(Version).where(Version.agent_id == aid).order_by(Version.version_number.desc())
    )
    return {**summary(a), "versions": [version_view(v) for v in versions]}


@router.get("/agents/{aid}/versions/{vid}")
def read_version(aid: UUID, vid: UUID, request: Request, s: DB):
    accessible(s, guest(request, s, False), aid)
    v = s.scalar(select(Version).where(Version.agent_id == aid, Version.id == vid))
    if not v:
        raise HTTPException(404)
    return version_view(v)


@router.patch("/agents/{aid}")
def edit(aid: UUID, data: MetadataPatch, request: Request, s: DB):
    a = accessible(s, guest(request, s), aid, True)
    if data.name is not None:
        a.name = data.name
    if data.description is not None:
        a.description = data.description
    return summary(a)


@router.post("/agents/{aid}/versions", status_code=201)
def version(aid: UUID, data: Configuration, request: Request, s: DB):
    return append(s, accessible(s, guest(request, s), aid, True), data)


def catalog():
    # Select public fields explicitly: evaluator rules never enter the response.
    return (
        select(
            Scenario.id,
            Scenario.name,
            Scenario.category,
            Scenario.severity,
            ScenarioVersion.version,
            ScenarioVersion.description,
        )
        .join(ScenarioVersion)
        .where(ScenarioVersion.version == 1)
    )


@router.get("/scenarios")
def scenarios(
    s: DB,
    q: Annotated[str, Query(max_length=80)] = "",
    category: Annotated[str, Query(max_length=80)] = "",
):
    stmt = catalog()
    if q:
        stmt = stmt.where(
            or_(
                Scenario.name.icontains(q, autoescape=True),
                Scenario.id.icontains(q, autoescape=True),
            )
        )
    if category:
        stmt = stmt.where(Scenario.category == category)
    return s.execute(stmt.order_by(Scenario.id)).mappings().all()


@router.get("/scenarios/{sid}")
def scenario(sid: str, s: DB):
    row = s.execute(catalog().where(Scenario.id == sid)).mappings().one_or_none()
    if not row:
        raise HTTPException(404)
    return dict(row)


@router.get("/scenario-suites")
def suites(s: DB):
    return [
        {
            "id": "core-v1",
            "members": [
                {"scenario_id": sid, "version": v}
                for sid, v in s.execute(
                    select(ScenarioVersion.scenario_id, ScenarioVersion.version)
                    .where(ScenarioVersion.version == 1)
                    .order_by(ScenarioVersion.scenario_id)
                )
            ],
        },
        {
            "id": SUITE,
            "members": [{"scenario_id": sid, "version": v} for sid, v in MEMBERS.items()],
        },
    ]
