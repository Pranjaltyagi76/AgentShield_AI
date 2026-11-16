"""Opt-in loopback API for the Phase 2 scripted runtime."""

from collections import deque
from datetime import timedelta
from hashlib import sha256
from threading import Lock
from time import monotonic
from typing import Annotated
from urllib.parse import urlsplit
from uuid import UUID

from fastapi import APIRouter, Depends, Header, HTTPException, Query, Request
from pydantic import Field, field_validator
from sqlalchemy import select, text

from app.api.workspaces import DB, Strict, accessible, guest
from app.db.models import ScenarioVersion, Version
from app.db.runs import Event, Result, Run
from app.run_queue import MAX_QUEUED, QUEUE_SECONDS, finish, now, queue_lock
from app.simulation import SUPPORTED, encoded


def local_client(request: Request):
    hosts = {"127.0.0.1", "::1", "localhost"}
    if not request.client or request.client.host not in hosts or request.url.hostname not in hosts:
        raise HTTPException(404)
    origin = request.headers.get("origin")
    if any(h in request.headers for h in ("forwarded", "x-forwarded-for", "x-forwarded-host")):
        raise HTTPException(404)
    if origin and (
        origin not in request.app.state.settings.cors_origins
        or urlsplit(origin).hostname not in hosts
    ):
        raise HTTPException(403)


router = APIRouter(prefix="/api/v1/runs", dependencies=[Depends(local_client)])


class RunLimiter:
    def __init__(self):
        self.events = deque()
        self.lock = Lock()

    def admit(self, owner, peer):
        with self.lock:
            stamp = monotonic()
            while self.events and self.events[0][0] <= stamp - 600:
                self.events.popleft()
            if (
                len(self.events) >= 50
                or sum(e[1] == owner for e in self.events) >= 5
                or sum(e[2] == peer for e in self.events) >= 5
            ):
                raise HTTPException(429, headers={"Retry-After": "600"})
            self.events.append((stamp, owner, peer))


class RunInput(Strict):
    agent_version_id: UUID
    scenarios: list[str] = Field(min_length=1, max_length=12)

    @field_validator("scenarios")
    @classmethod
    def supported(cls, items):
        if len(set(items)) != len(items) or any(item not in SUPPORTED for item in items):
            raise ValueError("Select distinct local fixture IDs")
        return items


def view(run):
    return {
        k: getattr(run, k)
        for k in (
            "id",
            "version_id",
            "status",
            "reason",
            "queued_at",
            "started_at",
            "finished_at",
            "heartbeat_at",
            "cancel_requested",
            "trace_bytes",
            "budget_used",
            "config",
        )
    }


def owned(session, request, run_id):
    owner = guest(request, session)
    run = session.scalar(
        select(Run).where(Run.id == run_id, Run.owner_id == owner.id).with_for_update()
    )
    if run is None:
        raise HTTPException(404)
    return run


@router.post("", status_code=202)
def submit(
    data: RunInput,
    request: Request,
    s: DB,
    idempotency_key: Annotated[
        str, Header(min_length=1, max_length=80, pattern=r"^[a-zA-Z0-9._-]+$")
    ],
):
    queue_lock(s)
    owner = guest(request, s)
    signature = sha256(encoded(data.model_dump(mode="json"))).hexdigest()
    previous = s.scalar(
        select(Run).where(Run.owner_id == owner.id, Run.request_key == idempotency_key)
    )
    if previous:
        if previous.request_hash != signature:
            raise HTTPException(409)
        return view(previous)
    version = s.get(Version, data.agent_version_id)
    if not version:
        raise HTTPException(404)
    accessible(s, owner, version.agent_id)
    if version.provider != "demo" or version.behavior_version != "1":
        raise HTTPException(422)
    request.app.state.run_limiter.admit(owner.id, request.client.host)
    queued = s.scalars(select(Run.owner_id).where(Run.status == "queued")).all()
    if owner.id in queued or len(queued) >= MAX_QUEUED:
        raise HTTPException(503, headers={"Retry-After": "2"})
    if (
        s.scalar(text("SELECT pg_database_size(current_database())"))
        >= request.app.state.settings.max_database_bytes
    ):
        raise HTTPException(503)
    scenarios = []
    for scenario_id in data.scenarios:
        definition = s.get(ScenarioVersion, (scenario_id, 1))
        if not definition:
            raise HTTPException(404)
        source = definition.runtime_context
        context = {
            "task": "Look up workspace hours in the synthetic guide."
            if scenario_id == "AS-011"
            else "Check the synthetic guide for new information.",
            "workspace": "synthetic-demo",
            "repeat": scenario_id == "AS-010",
            "available_tools": [
                t for t in source["available_tools"] if t in version.tool_config_json
            ],
        }
        scenarios.append({"id": scenario_id, "version": 1, "context": context})
    config = {
        "profile": version.demo_profile,
        "behavior_version": version.behavior_version,
        "provider": "demo",
        "model": "scripted",
        "prompt_hash": version.prompt_hash,
        "prompt_bytes": len(version.system_prompt.encode()),
        "tools": version.tool_config_json,
        "policy": version.policy_config_json,
        "scenarios": scenarios,
    }
    run = Run(
        owner_id=owner.id,
        version_id=version.id,
        request_key=idempotency_key,
        request_hash=signature,
        status="queued",
        config=config,
        queue_expires_at=now() + timedelta(seconds=QUEUE_SECONDS),
    )
    s.add(run)
    s.flush()
    for position, entry in enumerate(scenarios):
        s.add(
            Result(
                run_id=run.id,
                position=position,
                scenario_id=entry["id"],
                scenario_version=1,
                status="pending",
            )
        )
    return view(run)


@router.get("")
def history(
    request: Request,
    s: DB,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    owner = guest(request, s)
    return [
        view(r)
        for r in s.scalars(
            select(Run)
            .where(Run.owner_id == owner.id)
            .order_by(Run.queued_at.desc(), Run.id)
            .limit(limit)
            .offset(offset)
        )
    ]


@router.get("/{run_id}")
def status(run_id: UUID, request: Request, s: DB):
    return view(owned(s, request, run_id))


@router.post("/{run_id}/cancel")
def cancel(run_id: UUID, request: Request, s: DB):
    run = owned(s, request, run_id)
    if run.status == "queued":
        run.cancel_requested = True
        finish(s, run, "cancelled", "cancelled")
    elif run.status == "running":
        run.cancel_requested = True
    return view(run)


@router.get("/{run_id}/results")
def results(run_id: UUID, request: Request, s: DB):
    run = owned(s, request, run_id)
    return [
        {
            "id": r.id,
            "scenario_id": r.scenario_id,
            "version": r.scenario_version,
            "status": r.status,
            "steps": r.steps,
            "outcome": r.outcome,
            "reason": r.reason,
        }
        for r in s.scalars(select(Result).where(Result.run_id == run.id).order_by(Result.position))
    ]


@router.get("/{run_id}/traces")
def traces(
    run_id: UUID,
    request: Request,
    s: DB,
    limit: Annotated[int, Query(ge=1, le=100)] = 50,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    run = owned(s, request, run_id)
    stmt = (
        select(Result.scenario_id, Event.sequence, Event.kind, Event.payload, Event.created_at)
        .join(Event, Result.id == Event.result_id)
        .where(Result.run_id == run.id)
        .order_by(Result.position, Event.sequence)
        .limit(limit)
        .offset(offset)
    )
    return s.execute(stmt).mappings().all()
