"""Health is process-only. Readiness checks PostgreSQL, never inference."""

import logging
from typing import Literal

from fastapi import APIRouter, Request, Response
from pydantic import BaseModel

from app import __version__
from app.db.connection import DatabaseStatus

router = APIRouter(prefix="/api/v1", tags=["system"])
logger = logging.getLogger("agentshield")


class HealthResponse(BaseModel):
    status: Literal["ok"] = "ok"
    service: str = "agentshield-api"
    version: str = __version__
    public_runs_enabled: bool
    run_mode: Literal["local", "public", "disabled"]
    phase: Literal[6] = 6


class ReadinessResponse(BaseModel):
    status: Literal["ready", "not_ready"]
    database: DatabaseStatus
    service: str = "agentshield-api"
    phase: Literal[6] = 6


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
