"""Phase 0 application factory. No agent, scenario, or execution endpoints exist."""

import logging
from collections.abc import AsyncIterator
from contextlib import asynccontextmanager
from time import perf_counter
from uuid import uuid4

from fastapi import FastAPI, Request
from fastapi.exceptions import RequestValidationError
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import JSONResponse
from starlette.exceptions import HTTPException

from app import __version__
from app.api.system import router
from app.core.logging import configure_logging
from app.core.settings import Settings
from app.db.connection import Database, DatabaseProbe

logger = logging.getLogger("agentshield")


def error_response(request: Request, code: str, message: str, status: int) -> JSONResponse:
    return JSONResponse(
        {"error": {"code": code, "message": message, "request_id": request.state.request_id}},
        status_code=status,
    )


def create_app(settings: Settings | None = None, database: DatabaseProbe | None = None) -> FastAPI:
    config = settings or Settings()
    configure_logging(config.log_level)
    probe = database if database is not None else Database(config)

    @asynccontextmanager
    async def lifespan(application: FastAPI) -> AsyncIterator[None]:
        logger.info("application_started")
        try:
            yield
        finally:
            probe.close()
            logger.info("application_stopped")

    application = FastAPI(
        title="AgentShield AI",
        description="Synthetic agent-security evaluation platform. Phase 0 foundation only.",
        version=__version__,
        docs_url="/docs" if config.app_env != "production" else None,
        redoc_url=None,
        openapi_url="/openapi.json" if config.app_env != "production" else None,
        lifespan=lifespan,
    )
    application.state.database = probe
    application.state.settings = config

    @application.middleware("http")
    async def request_context(request: Request, call_next):
        request.state.request_id = str(uuid4())
        started = perf_counter()
        try:
            response = await call_next(request)
        except Exception:
            logger.error("unhandled_request_error", extra={"request_id": request.state.request_id})
            response = error_response(
                request, "internal_error", "An unexpected server error occurred.", 500
            )
        response.headers["X-Request-ID"] = request.state.request_id
        response.headers["X-Content-Type-Options"] = "nosniff"
        response.headers["Referrer-Policy"] = "no-referrer"
        response.headers["Cache-Control"] = "no-store"
        logger.info(
            "request_completed",
            extra={
                "request_id": request.state.request_id,
                "method": request.method,
                "status_code": response.status_code,
                "duration_ms": round((perf_counter() - started) * 1000, 2),
            },
        )
        return response

    @application.exception_handler(HTTPException)
    async def http_error(request: Request, exception: HTTPException) -> JSONResponse:
        code = "not_found" if exception.status_code == 404 else "http_error"
        message = "Resource not found." if exception.status_code == 404 else "Request not allowed."
        return error_response(request, code, message, exception.status_code)

    @application.exception_handler(RequestValidationError)
    async def validation_error(request: Request, exception: RequestValidationError) -> JSONResponse:
        return error_response(request, "validation_error", "Request validation failed.", 422)

    application.include_router(router)
    application.add_middleware(
        CORSMiddleware,
        allow_origins=config.cors_origins,
        allow_credentials=False,
        allow_methods=["GET"],
        allow_headers=["Content-Type"],
        expose_headers=["X-Request-ID"],
    )
    return application


app = create_app()
