"""Health is process-only. Readiness checks PostgreSQL, never inference."""

import logging
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app import __version__
from app.custom_scenarios import MAX_CUSTOM_SCENARIOS, MAX_CUSTOM_VERSIONS
from app.db.connection import DatabaseStatus
from app.policy import MAX_CALLS
from app.run_queue import MAX_ACTIVE, MAX_QUEUED, MAX_STEPS, MAX_TOTAL, MAX_TRACE

router = APIRouter(prefix="/api/v1", tags=["system"])
logger = logging.getLogger("agentshield")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "agentshield-api"
    version: str = __version__
    public_runs_enabled: bool
    run_mode: Literal["local", "public", "disabled"]
    phase: Literal[8] = 8


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    database: DatabaseStatus
    service: str = "agentshield-api"
    phase: Literal[8] = 8


class InferenceStatus(BaseModel):
    provider: Literal["gemini"] = "gemini"
    enabled: Literal[False] = False
    reason: Literal["free_account_access_unverified"] = "free_account_access_unverified"
    model: None = None


class DemoStatus(BaseModel):
    execution_enabled: bool
    profiles: tuple[Literal["vulnerable"], Literal["hardened"]] = ("vulnerable", "hardened")
    requires_api_key: Literal[False] = False
    inference: InferenceStatus = InferenceStatus()
    custom_scenarios_enabled: Literal[True] = True
    limits: dict[str, int]


@router.get("/demo/status", response_model=DemoStatus)
def demo_status(request: Request) -> DemoStatus:
    """Report release capabilities without probing accounts or invoking inference.

    execution_enabled is the operator flag. Database availability is reported by /ready.
    Phase 7 follows the specification's explicit disabled-inference exit branch.
    """
    settings = request.app.state.settings
    return DemoStatus(
        execution_enabled=settings.local_runs_enabled or settings.public_runs_enabled,
        limits={
            "scenarios_per_run": 12,
            "active_runs_global": MAX_ACTIVE,
            "queued_runs_global": MAX_QUEUED,
            "steps_per_scenario": MAX_STEPS,
            "calls_per_scenario": MAX_CALLS,
            "trace_bytes_per_run": MAX_TRACE,
            "scripted_bytes_per_run": MAX_TOTAL,
            "guest_retention_days": 7,
            "custom_scenarios_per_guest": MAX_CUSTOM_SCENARIOS,
            "versions_per_custom_scenario": MAX_CUSTOM_VERSIONS,
            "database_admission_bytes": settings.max_database_bytes,
        },
    )


@router.get("/health", response_model=HealthResponse)
def health(request: Request) -> HealthResponse:
    settings = request.app.state.settings
    mode = (
        "public"
        if settings.public_runs_enabled
        else "local"
        if settings.local_runs_enabled
        else "disabled"
    )
    return HealthResponse(public_runs_enabled=settings.public_runs_enabled, run_mode=mode)


@router.get(
    "/ready",
    response_model=ReadinessResponse,
    responses={503: {"model": ReadinessResponse, "description": "Database is not ready"}},
)
def ready(request: Request, response: Response) -> ReadinessResponse:
    try:
        database_status = request.app.state.database.check()
    except Exception:
        # Driver exceptions can contain credentials/hosts; never expose or log their text.
        logger.warning("database_probe_failed", extra={"request_id": request.state.request_id})
        database_status = "unavailable"
    is_ready = database_status == "connected"
    response.status_code = 200 if is_ready else 503
    return ReadinessResponse(status="ready" if is_ready else "not_ready", database=database_status)
