"""Versioned report rendering from retained evidence, without local artifacts."""

import json
from collections import Counter
from html import escape

from fastapi.encoders import jsonable_encoder
from sqlalchemy import select

from app.api.runs import run_results
from app.db.runs import Comparison, Event, Result
from app.evaluation import metrics
from app.suite import redact

RENDERER_VERSION = "1"
LIMITATIONS = [
    "Scripted synthetic evaluation with mock tools. "
    "These results do not measure real-model security.",
    "Coverage and applicability limit each metric. Empty denominators are unavailable.",
    "Inconclusive scenarios retain partial evidence and are excluded from pass/fail rates.",
    "Downloads can be regenerated only while the guest and all source records remain retained.",
    "Recommendations describe the recorded evidence and do not establish complete security.",
]


def build_report(session, report, run):
    results = run_results(session, run)
    findings = [
        {"scenario_id": r.scenario_id, "scenario_version": r.scenario_version, **f}
        for r in results
        if r.assessment
        for f in r.assessment.get("findings", [])
    ]
    events = session.execute(
        select(
            Result.scenario_id,
            Event.id,
            Event.sequence,
            Event.kind,
            Event.payload,
            Event.created_at,
        )
        .join(Event, Event.result_id == Result.id)
        .where(Result.run_id == run.id)
        .order_by(Result.position, Event.sequence)
    ).mappings()
    comparison = session.get(Comparison, report.comparison_id) if report.comparison_id else None
    return redact(
        jsonable_encoder(
            {
                "format_version": 1,
                "renderer_version": report.renderer_version,
                "report_id": report.id,
                "created_at": report.created_at,
                "run": {
                    "id": run.id,
                    "agent_version_id": run.version_id,
                    "status": run.status,
                    "reason": run.reason,
                    "queued_at": run.queued_at,
                    "started_at": run.started_at,
                    "finished_at": run.finished_at,
                    "configuration": run.config,
                },
                "metrics": metrics(results),
                "severity_breakdown": dict(Counter(f["severity"] for f in findings)),
                "scenarios": [
                    {
                        "scenario_id": r.scenario_id,
                        "version": r.scenario_version,
                        "status": r.status,
                        "outcome": r.outcome or "inconclusive",
                        "reason": r.reason,
                        "evaluation_reason": r.assessment.get("reason")
                        if r.assessment
                        else "missing_assessment",
                    }
                    for r in results
                ],
                "failed_scenarios": [r.scenario_id for r in results if r.outcome == "fail"],
                "findings": findings,
                "evidence": [dict(e) for e in events],
                "comparison": comparison.comparison_json if comparison else None,
                "limitations": LIMITATIONS,
            }
        )
    )


def render_json(report):
    return json.dumps(report, ensure_ascii=False, indent=2)


def render_html(report):
    def text(value):
        return escape(str(value), quote=True)

    sections = []
    for heading, value in report.items():
        if heading == "metrics":
            rows = []
            for name, metric in value.items():
                if isinstance(metric, dict) and "numerator" in metric:
                    count = f"{metric['numerator']}/{metric['denominator']}"
                    percent = "N/A" if metric["percent"] is None else f"{metric['percent']}%"
                else:
                    count, percent = metric, "—"
                rows.append(
                    "<tr><th>"
                    + text(name.replace("_", " "))
                    + "</th><td>"
                    + text(count)
                    + "</td><td>"
                    + text(percent)
                    + "</td></tr>"
                )
            sections.append(
                "<section><h2>Metrics</h2><table><thead><tr><th>Metric</th>"
                "<th>Count</th><th>Rate</th></tr></thead><tbody>"
                + "".join(rows)
                + "</tbody></table></section>"
            )
        elif heading == "limitations":
            sections.append(
                "<section><h2>Limitations</h2><ul>"
                + "".join("<li>" + text(item) + "</li>" for item in value)
                + "</ul></section>"
            )
        elif heading == "evidence":
            entries = "".join(
                '<article id="event-'
                + text(e["id"])
                + '"><h3>'
                + text(e["scenario_id"])
                + " · "
                + text(e["sequence"])
                + " · "
                + text(e["kind"])
                + "</h3><pre>"
                + text(render_json(e))
                + "</pre></article>"
                for e in value
            )
            sections.append("<section><h2>Evidence</h2>" + entries + "</section>")
        elif heading == "findings":
            entries = "".join(
                "<li>"
                + text(f["scenario_id"])
                + " · "
                + text(f["severity"])
                + " · "
                + text(f["summary"])
                + "<p>"
                + text(f["remediation"])
                + '</p><a href="#event-'
                + text(f["evidence_id"])
                + '">Recorded evidence</a></li>'
                for f in value
            )
            sections.append("<section><h2>Findings</h2><ul>" + entries + "</ul></section>")
        else:
            sections.append(
                "<section><h2>"
                + text(heading.replace("_", " ").capitalize())
                + "</h2><pre>"
                + text(render_json(value))
                + "</pre></section>"
            )
    return (
        '<!doctype html><html lang="en"><head><meta charset="utf-8">'
        + '<meta name="viewport" content="width=device-width, initial-scale=1">'
        + '<meta http-equiv="Content-Security-Policy" content="default-src \'none\'; '
        + "style-src 'unsafe-inline'; base-uri 'none'; form-action 'none'\">"
        + "<title>AgentShield evaluation report</title><style>"
        + "body{max-width:960px;margin:2rem auto;padding:0 1rem;"
        + "font-family:system-ui;line-height:1.6}"
        + "pre{white-space:pre-wrap;overflow-wrap:anywhere;background:#f4f5f7;padding:1rem}"
        + "section{margin:2rem 0}a{color:#244aaf}article{border-top:1px solid #ddd}"
        + "table{border-collapse:collapse;width:100%}th,td{text-align:left;"
        + "padding:.5rem;border-bottom:1px solid #ddd}"
        + "</style></head><body>"
        + (
            "<h1>Saved sample - not a live run</h1>"
            if report.get("sample")
            else "<h1>AgentShield evaluation report</h1>"
        )
        + "".join(sections)
        + "</body></html>"
    )
