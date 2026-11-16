"""Database-backed local queue. Commit each scripted step and its trace atomically."""

import logging
from copy import deepcopy
from datetime import UTC, datetime, timedelta
from threading import Event as StopSignal
from uuid import uuid4

from sqlalchemy import select, text
from sqlalchemy.exc import SQLAlchemyError
from sqlalchemy.orm import Session

from app.db.models import Guest
from app.db.runs import Event, Result, Run
from app.simulation import decide, encoded, gateway

MAX_ACTIVE = 2
MAX_QUEUED = 10
MAX_TRACE = 1048576
MAX_EVENT = 16384
MAX_INPUT = 4000
MAX_OUTPUT = 512
MAX_TOTAL = 20000
MAX_STEPS = 10
RUN_SECONDS = 180
SCENARIO_SECONDS = 60
QUEUE_SECONDS = 300


def now():
    return datetime.now(UTC)


def queue_lock(session):
    session.execute(text("SELECT pg_advisory_xact_lock(19485122)"))


def finish(session, run, status, reason):
    run.status = status
    run.reason = reason
    run.finished_at = now()
    for result in session.scalars(
        select(Result).where(Result.run_id == run.id, Result.status.in_(("pending", "running")))
    ):
        result.status = status
        result.reason = reason
        result.outcome = "inconclusive"


def lock_run(session, run_id):
    # Revocation and cleanup lock the parent before cascading to child rows.
    owner_id = session.scalar(select(Run.owner_id).where(Run.id == run_id))
    if owner_id is None:
        return None
    owner = session.scalar(
        select(Guest).where(Guest.id == owner_id).with_for_update(key_share=True)
    )
    if owner is None:
        return None
    return session.scalar(select(Run).where(Run.id == run_id).with_for_update())


def recover(session):
    queue_lock(session)
    for run_id in session.scalars(select(Run.id).where(Run.status == "running")):
        run = lock_run(session, run_id)
        if run and run.status == "running":
            finish(session, run, "failed", "interrupted")


def claim(session, worker):
    queue_lock(session)
    for run_id in session.scalars(
        select(Run.id).where(Run.status == "queued").order_by(Run.queued_at, Run.id)
    ):
        candidate = lock_run(session, run_id)
        if not candidate or candidate.status != "queued":
            continue
        owner = session.get(Guest, candidate.owner_id)
        if candidate.queue_expires_at <= now() or not owner or owner.expires_at <= now():
            finish(session, candidate, "failed", "expired")
            continue
        active = session.scalars(select(Run.owner_id).where(Run.status == "running")).all()
        if len(active) >= MAX_ACTIVE or candidate.owner_id in active:
            continue
        candidate.worker_id = worker
        candidate.started_at = candidate.heartbeat_at = now()
        candidate.status = "running"
        return candidate.id
    return None


class BudgetStop(Exception):
    pass


def record(session, run, result, events):
    sizes = [len(encoded({"kind": kind, "payload": payload})) for kind, payload in events]
    if any(size > MAX_EVENT for size in sizes) or run.trace_bytes + sum(sizes) > MAX_TRACE:
        raise BudgetStop("trace_limit")
    for kind, payload in events:
        session.add(
            Event(result_id=result.id, sequence=result.next_sequence, kind=kind, payload=payload)
        )
        result.next_sequence += 1
    run.trace_bytes += sum(sizes)


def execute_step(session, run, result):
    config = run.config
    entry = config["scenarios"][result.position]
    context = entry["context"]
    if result.started_at is None:
        result.started_at = now()
        result.status = "running"
        record(
            session,
            run,
            result,
            [
                ("scenario_start", {"id": result.scenario_id, "version": result.scenario_version}),
                ("agent_input", context),
            ],
        )
    if now() - result.started_at >= timedelta(seconds=SCENARIO_SECONDS):
        raise BudgetStop("scenario_timeout")
    if result.steps >= MAX_STEPS:
        raise BudgetStop("step_limit")
    # Scripted calls use no provider tokens. UTF-8 bytes conservatively bound text budgets.
    input_size = (
        len(encoded(context)) + len(encoded(result.last_observation)) + config["prompt_bytes"]
    )
    if input_size > MAX_INPUT or run.budget_used + input_size > MAX_TOTAL:
        raise BudgetStop("input_budget")
    permitted_tools = tuple(context["available_tools"])
    action = decide(
        config["profile"], deepcopy(context), deepcopy(result.last_observation), result.steps
    )
    output_size = len(encoded(action))
    if output_size > MAX_OUTPUT or run.budget_used + input_size + output_size > MAX_TOTAL:
        raise BudgetStop("output_budget")
    if "tool" in action:
        decision, response = gateway(action["tool"], action["arguments"], permitted_tools)
        events = [("tool_requested", action), ("policy_decision", {"decision": decision})]
        if response is not None:
            events.append(("mock_tool_result", response))
        record(session, run, result, events)
        result.last_observation = response or {"decision": decision}
    else:
        record(
            session,
            run,
            result,
            [("agent_output", action), ("scenario_end", {"status": "completed"})],
        )
        result.status = "completed"
    result.steps += 1
    run.budget_used += input_size + output_size


def advance(session, run_id, worker):
    run = lock_run(session, run_id)
    if run is None or run.status != "running" or run.worker_id != worker:
        return
    run.heartbeat_at = now()
    owner = session.get(Guest, run.owner_id)
    if not owner or owner.expires_at <= now():
        finish(session, run, "failed", "expired")
    elif run.cancel_requested:
        finish(session, run, "cancelled", "cancelled")
    elif now() - run.started_at >= timedelta(seconds=RUN_SECONDS):
        finish(session, run, "failed", "run_timeout")
    else:
        result = session.scalar(
            select(Result)
            .where(Result.run_id == run.id, Result.status != "completed")
            .order_by(Result.position)
            .limit(1)
        )
        if result is None:
            finish(session, run, "completed", None)
            return
        try:
            execute_step(session, run, result)
        except BudgetStop as stop:
            finish(session, run, "failed", str(stop))
        else:
            if result.status == "completed" and result.position == len(run.config["scenarios"]) - 1:
                finish(session, run, "completed", None)


def tick(engine, worker):
    with Session(engine) as session, session.begin():
        claim(session, worker)
        active = session.scalars(
            select(Run.id).where(Run.worker_id == worker, Run.status == "running")
        ).all()
    for run_id in active:
        try:
            with Session(engine) as session, session.begin():
                advance(session, run_id, worker)
        except SQLAlchemyError:
            raise
        except Exception:
            logging.getLogger("agentshield").error("scripted_step_failed")
            with Session(engine) as session, session.begin():
                run = lock_run(session, run_id)
                if run and run.worker_id == worker and run.status == "running":
                    finish(session, run, "failed", "runtime_error")


def consume(engine, stop: StopSignal):
    """Run all worker transactions on the connection holding the leadership lock."""
    worker = uuid4()
    while not stop.is_set():
        try:
            with engine.connect() as leader:
                elected = leader.scalar(text("SELECT pg_try_advisory_lock(19485123)"))
                leader.commit()
                if elected:
                    try:
                        with Session(leader) as session, session.begin():
                            recover(session)
                        while not stop.is_set():
                            tick(leader, worker)
                            stop.wait(0.15)
                    finally:
                        if not leader.invalidated:
                            leader.execute(text("SELECT pg_advisory_unlock(19485123)"))
                            leader.commit()
        except SQLAlchemyError:
            logging.getLogger("agentshield").warning("local_queue_unavailable")
        stop.wait(1)
