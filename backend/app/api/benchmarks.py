"""Guest-owned, retry-safe benchmark comparisons."""

from uuid import UUID

from fastapi import APIRouter, Depends, HTTPException, Request, Response
from sqlalchemy import func, select, text
from sqlalchemy.orm import aliased

from app.api.runs import execution_client, run_results
from app.api.workspaces import DB, Strict, guest
from app.comparison import compare_runs
from app.db.runs import Comparison, Run

router = APIRouter(prefix="/api/v1/benchmarks", dependencies=[Depends(execution_client)])
MAX_COMPARISONS_PER_GUEST = 64


class Pair(Strict):
    baseline_run_id: UUID
    candidate_run_id: UUID


def view(record):
    return {"id": record.id, "created_at": record.created_at, **record.comparison_json}


@router.post("/compare", status_code=201)
def create(data: Pair, request: Request, response: Response, s: DB):
    # guest() locks the guest row for the transaction, including admission and insertion.
    owner = guest(request, s)
    if data.baseline_run_id == data.candidate_run_id:
        raise HTTPException(422)
    runs = {
        r.id: r
        for r in s.scalars(
            select(Run)
            .where(
                Run.owner_id == owner.id, Run.id.in_([data.baseline_run_id, data.candidate_run_id])
            )
            .order_by(Run.id)
            .with_for_update(read=True)
        )
    }
    if len(runs) != 2:
        raise HTTPException(404)
    existing = s.scalar(
        select(Comparison).where(
            Comparison.baseline_run_id == data.baseline_run_id,
            Comparison.candidate_run_id == data.candidate_run_id,
        )
    )
    if existing:
        response.status_code = 200
        return view(existing)
    first, second = runs[data.baseline_run_id], runs[data.candidate_run_id]
    if any(r.status not in ("completed", "failed", "cancelled") for r in (first, second)):
        raise HTTPException(409)
    count = s.scalar(
        select(func.count())
        .select_from(Comparison)
        .join(Run, Run.id == Comparison.baseline_run_id)
        .where(Run.owner_id == owner.id)
    )
    if (
        count >= MAX_COMPARISONS_PER_GUEST
        or s.scalar(text("SELECT pg_database_size(current_database())"))
        >= request.app.state.settings.max_database_bytes
    ):
        raise HTTPException(503)
    record = Comparison(
        baseline_run_id=first.id,
        candidate_run_id=second.id,
        comparison_json=compare_runs(first, second, run_results(s, first), run_results(s, second)),
    )
    s.add(record)
    s.flush()
    return view(record)


@router.get("/{comparison_id}")
def get(comparison_id: UUID, request: Request, s: DB):
    owner = guest(request, s)
    candidate = aliased(Run)
    record = s.scalar(
        select(Comparison)
        .join(Run, Run.id == Comparison.baseline_run_id)
        .join(candidate, candidate.id == Comparison.candidate_run_id)
        .where(
            Comparison.id == comparison_id, Run.owner_id == owner.id, candidate.owner_id == owner.id
        )
    )
    if record is None:
        raise HTTPException(404)
    return view(record)
