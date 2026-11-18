"""Owned authoring, validation and append-only versions with persistent quotas."""

from uuid import uuid4

from fastapi import APIRouter, HTTPException, Request
from sqlalchemy import func, select, text

from app.api.workspaces import DB, guest
from app.custom_scenarios import (
    MAX_CUSTOM_SCENARIOS,
    MAX_CUSTOM_VERSIONS,
    CustomDraft,
    CustomId,
    compile_definition,
    definition_hash,
)
from app.db.models import CustomScenario, CustomScenarioVersion
from app.policy import encoded

router = APIRouter(prefix="/api/v1/custom-scenarios")


def view(version):
    return {
        key: getattr(version, key)
        for key in (
            "scenario_id",
            "version",
            "name",
            "description",
            "definition",
            "definition_hash",
            "created_at",
        )
    }


def owned(session, owner, sid):
    record = session.scalar(
        select(CustomScenario).where(CustomScenario.id == sid, CustomScenario.owner_id == owner.id)
    )
    if record is None:
        raise HTTPException(404)
    return record


def storage(request, session):
    if (
        session.scalar(text("SELECT pg_database_size(current_database())"))
        >= request.app.state.settings.max_database_bytes
    ):
        raise HTTPException(503)


def append(session, sid, draft):
    version = 1 + (
        session.scalar(
            select(func.max(CustomScenarioVersion.version)).where(
                CustomScenarioVersion.scenario_id == sid
            )
        )
        or 0
    )
    if version > MAX_CUSTOM_VERSIONS:
        raise HTTPException(409)
    record = CustomScenarioVersion(
        scenario_id=sid,
        version=version,
        name=draft.name,
        description=draft.description,
        definition=draft.definition.model_dump(),
        definition_hash=definition_hash(draft),
    )
    session.add(record)
    session.flush()
    return view(record)


@router.post("/validate")
def validate(data: CustomDraft, request: Request, s: DB):
    guest(request, s)
    context, _ = compile_definition(data.definition)
    return {
        "valid": True,
        "definition_hash": definition_hash(data),
        "runtime_context_bytes": len(encoded(context)),
        "checker": data.definition.checker,
    }


@router.get("")
def history(request: Request, s: DB):
    owner = guest(request, s)
    latest = (
        select(
            CustomScenarioVersion.scenario_id,
            func.max(CustomScenarioVersion.version).label("version"),
        )
        .group_by(CustomScenarioVersion.scenario_id)
        .subquery()
    )
    records = s.scalars(
        select(CustomScenarioVersion)
        .join(CustomScenario)
        .join(
            latest,
            (latest.c.scenario_id == CustomScenarioVersion.scenario_id)
            & (latest.c.version == CustomScenarioVersion.version),
        )
        .where(CustomScenario.owner_id == owner.id)
        .order_by(CustomScenario.created_at, CustomScenario.id)
    )
    return [
        {
            "id": v.scenario_id,
            "version": v.version,
            "name": v.name,
            "description": v.description,
            "checker": v.definition["checker"],
        }
        for v in records
    ]


@router.post("", status_code=201)
def create(data: CustomDraft, request: Request, s: DB):
    owner = guest(request, s)
    if (
        s.scalar(
            select(func.count())
            .select_from(CustomScenario)
            .where(CustomScenario.owner_id == owner.id)
        )
        >= MAX_CUSTOM_SCENARIOS
    ):
        raise HTTPException(409)
    storage(request, s)
    sid = "CS-" + uuid4().hex
    s.add(CustomScenario(id=sid, owner_id=owner.id))
    s.flush()
    return {"id": sid, "versions": [append(s, sid, data)]}


@router.get("/{sid}")
def detail(sid: CustomId, request: Request, s: DB):
    owned(s, guest(request, s), sid)
    versions = s.scalars(
        select(CustomScenarioVersion)
        .where(CustomScenarioVersion.scenario_id == sid)
        .order_by(CustomScenarioVersion.version.desc())
    )
    return {"id": sid, "versions": [view(v) for v in versions]}


@router.post("/{sid}/versions", status_code=201)
def version(sid: CustomId, data: CustomDraft, request: Request, s: DB):
    owned(s, guest(request, s), sid)
    storage(request, s)
    return append(s, sid, data)
