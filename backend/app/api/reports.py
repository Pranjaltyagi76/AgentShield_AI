"""Bounded, owned report metadata and on-demand download."""

from typing import Annotated, Literal
from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Query, Request, Response
from sqlalchemy import func, select, text

from app.api.runs import execution_client
from app.api.workspaces import DB, Strict, guest
from app.db.runs import Comparison, Report, Run
from app.reporting import RENDERER_VERSION, build_report, render_html, render_json

router = APIRouter(prefix="/api/v1", dependencies=[Depends(execution_client)])
MAX_REPORTS_PER_GUEST = 64


class ReportInput(Strict):
    format: Literal["html", "json"]
    comparison_id: UUID | None = None


def view(record):
    return {
        k: getattr(record, k)
        for k in ("id", "run_id", "comparison_id", "format", "renderer_version", "created_at")
    }


def check_comparison(session, owner, comparison_id, run_id):
    comparison = session.get(Comparison, comparison_id)
    if comparison is None or run_id not in (
        comparison.baseline_run_id,
        comparison.candidate_run_id,
    ):
        raise HTTPException(404)
    ids = (comparison.baseline_run_id, comparison.candidate_run_id)
    if (
        session.scalar(
            select(func.count()).select_from(Run).where(Run.id.in_(ids), Run.owner_id == owner.id)
        )
        != 2
    ):
        raise HTTPException(404)


def source(session, owner, run_id):
    run = session.scalar(
        select(Run).where(Run.id == run_id, Run.owner_id == owner.id).with_for_update(read=True)
    )
    if run is None:
        raise HTTPException(404)
    return run


@router.post("/runs/{run_id}/reports", status_code=201)
def create(run_id: UUID, data: ReportInput, request: Request, response: Response, s: DB):
    owner = guest(request, s)
    run = source(s, owner, run_id)
    if data.comparison_id:
        check_comparison(s, owner, data.comparison_id, run_id)
    if run.status not in ("completed", "failed", "cancelled"):
        raise HTTPException(409)
    existing = s.scalar(
        select(Report).where(
            Report.run_id == run_id,
            Report.comparison_id == data.comparison_id,
            Report.format == data.format,
            Report.renderer_version == RENDERER_VERSION,
        )
    )
    if existing:
        response.status_code = 200
        return view(existing)
    count = s.scalar(
        select(func.count())
        .select_from(Report)
        .join(Run, Report.run_id == Run.id)
        .where(Run.owner_id == owner.id)
    )
    if (
        count >= MAX_REPORTS_PER_GUEST
        or s.scalar(text("SELECT pg_database_size(current_database())"))
        >= request.app.state.settings.max_database_bytes
    ):
        raise HTTPException(503)
    record = Report(
        run_id=run.id,
        comparison_id=data.comparison_id,
        format=data.format,
        renderer_version=RENDERER_VERSION,
    )
    s.add(record)
    s.flush()
    return view(record)


@router.get("/reports")
def history(
    request: Request,
    s: DB,
    limit: Annotated[int, Query(ge=1, le=50)] = 20,
    offset: Annotated[int, Query(ge=0)] = 0,
):
    owner = guest(request, s)
    records = s.scalars(
        select(Report)
        .join(Run, Report.run_id == Run.id)
        .where(Run.owner_id == owner.id)
        .order_by(Report.created_at.desc(), Report.id)
        .limit(limit)
        .offset(offset)
    ).all()
    for record in records:
        if record.comparison_id:
            check_comparison(s, owner, record.comparison_id, record.run_id)
    return [view(r) for r in records]


def owned(report_id, request, session):
    owner = guest(request, session)
    record = session.get(Report, report_id)
    if record is None:
        raise HTTPException(404)
    run = source(session, owner, record.run_id)
    if record.comparison_id:
        check_comparison(session, owner, record.comparison_id, record.run_id)
    if record.renderer_version != RENDERER_VERSION:
        raise HTTPException(409)
    return record, run


@router.get("/reports/{report_id}")
def metadata(report_id: UUID, request: Request, s: DB):
    record, _ = owned(report_id, request, s)
    return view(record)


@router.get("/reports/{report_id}/download")
def download(report_id: UUID, request: Request, s: DB):
    record, run = owned(report_id, request, s)
    payload = build_report(s, record, run)
    body = render_html(payload) if record.format == "html" else render_json(payload)
    return Response(
        body,
        media_type="text/html" if record.format == "html" else "application/json",
        headers={
            "Content-Disposition": (
                f'attachment; filename="agentshield-{record.id}.{record.format}"'
            ),
            "Content-Security-Policy": (
                "sandbox; default-src 'none'; style-src 'unsafe-inline'; "
                "base-uri 'none'; form-action 'none'"
            ),
            "X-Content-Type-Options": "nosniff",
        },
    )
