"""Compare immutable scripted observations over a common, evaluable cohort."""

from collections import Counter

from app.evaluation import metrics, rate

SETTINGS = (
    "oracle_version",
    "runtime_version",
    "tool_schema_hash",
    "policy",
    "limits",
    "provider",
    "model",
    "tools",
)
VARIATIONS = ("profile", "behavior_version", "prompt_hash", "source_revision")
CATEGORIES = ("improved", "regressed", "unchanged", "inconclusive", "incompatible", "unmatched")


def normalized(key, value):
    if key in ("tools", "available_tools") and isinstance(value, list):
        return sorted(value)
    return value


def setting_issues(left, right):
    issues = []
    for key in SETTINGS:
        if any(cfg.get(key) is None or cfg.get(key) == "" for cfg in (left, right)):
            issues.append(f"missing_{key}")
        elif normalized(key, left[key]) != normalized(key, right[key]):
            issues.append(key)
    for key, required in (
        ("policy", {"version", "max_calls"}),
        ("limits", {"steps", "calls", "total_bytes", "run_seconds"}),
    ):
        if key not in issues and any(
            not isinstance(cfg.get(key), dict) or not required.issubset(cfg[key])
            for cfg in (left, right)
        ):
            issue = f"missing_{key}"
            if issue not in issues:
                issues.append(issue)
    for key in ("profile", "behavior_version", "prompt_hash"):
        if not left.get(key) or not right.get(key):
            issues.append(f"missing_{key}")
    if left.get("provider") != "demo" or right.get("provider") != "demo":
        issues.append("unsupported_execution_mode")
    return issues


def scenario_settings(config, entry):
    context = entry.get("context")
    if not isinstance(context, dict) or "available_tools" not in context:
        return None
    approval = config.get("confirmation")
    return (
        {**context, "available_tools": normalized("available_tools", context["available_tools"])},
        approval if approval and approval.get("scenario") == entry["id"] else None,
    )


def side(entry, result):
    if entry is None:
        return None
    outcome = "inconclusive"
    reason = "missing_result"
    if result is not None:
        reason = result.reason or (result.assessment or {}).get("reason")
        if (
            result.status == "completed"
            and result.assessment
            and result.scenario_version == entry["version"]
            and result.assessment.get("outcome") == result.outcome
            and result.outcome in ("pass", "fail")
        ):
            outcome = result.outcome
        elif not reason:
            reason = "missing_assessment"
    return {"version": entry["version"], "outcome": outcome, "reason": reason}


def delta(first, second):
    change = None
    if first["denominator"] and second["denominator"]:
        change = round(
            100
            * (
                second["numerator"] / second["denominator"]
                - first["numerator"] / first["denominator"]
            ),
            2,
        )
    return {"baseline": first, "candidate": second, "delta_pp": change}


def pair_issues(configs, entries, results, global_issues):
    reasons = list(global_issues)
    if entries[0]["version"] != entries[1]["version"]:
        reasons.append("scenario_version")
    if any(entry.get("definition_hash") is not None for entry in entries) and (
        not all(entry.get("definition_hash") for entry in entries)
        or entries[0]["definition_hash"] != entries[1]["definition_hash"]
        or entries[0].get("checker") != entries[1].get("checker")
    ):
        reasons.append("custom_definition")
    if any(
        result and result.scenario_version != entry["version"]
        for entry, result in zip(entries, results, strict=True)
    ):
        reasons.append("result_version")
    first, second = (
        scenario_settings(cfg, entry) for cfg, entry in zip(configs, entries, strict=True)
    )
    if first is None or second is None:
        reasons.append("missing_scenario_context")
    else:
        if first[0] != second[0]:
            reasons.append("scenario_context")
        if first[1] != second[1]:
            reasons.append("confirmation")
    return reasons


def compare_runs(baseline, candidate, baseline_results, candidate_results):
    left, right = baseline.config, candidate.config
    issues = setting_issues(left, right)
    manifests = [{e["id"]: e for e in cfg["scenarios"]} for cfg in (left, right)]
    indexes = [
        {r.scenario_id: r for r in results} for results in (baseline_results, candidate_results)
    ]
    cohorts = ([], [])
    covered = [0, 0]
    compatible_covered = [0, 0]
    compatible = 0
    rows = []
    for sid in dict.fromkeys([*manifests[0], *manifests[1]]):
        entries = [m.get(sid) for m in manifests]
        results = [idx.get(sid) for idx in indexes]
        sides = [side(entry, result) for entry, result in zip(entries, results, strict=True)]
        valid = [bool(s and s["outcome"] in ("pass", "fail")) for s in sides]
        for i in range(2):
            covered[i] += valid[i]
        reasons = []
        if None in entries:
            category = "unmatched"
        else:
            reasons = pair_issues((left, right), entries, results, issues)
            if reasons:
                category = "incompatible"
            else:
                compatible += 1
                for i in range(2):
                    compatible_covered[i] += valid[i]
                if not all(valid):
                    category = "inconclusive"
                else:
                    for i in range(2):
                        cohorts[i].append(results[i])
                    if sides[0]["outcome"] == sides[1]["outcome"]:
                        category = "unchanged"
                    else:
                        category = "improved" if sides[1]["outcome"] == "pass" else "regressed"
        rows.append(
            {
                "scenario_id": sid,
                "baseline": sides[0],
                "candidate": sides[1],
                "classification": category,
                "issues": reasons,
            }
        )
    before, after = (metrics(group) for group in cohorts)
    rates = {
        key: delta(value, after[key])
        for key, value in before.items()
        if isinstance(value, dict) and key != "coverage"
    }
    rates["coverage"] = delta(*(rate(n, compatible, 0) for n in compatible_covered))
    counts = Counter(row["classification"] for row in rows)

    def summary(run, index):
        config = run.config
        return {
            "id": str(run.id),
            "agent_version_id": str(run.version_id),
            "status": run.status,
            "profile": config.get("profile"),
            "behavior_version": config.get("behavior_version"),
            "prompt_hash": config.get("prompt_hash"),
            "source_revision": config.get("source_revision"),
            "coverage": rate(covered[index], len(manifests[index]), 0),
        }

    return {
        "format_version": 1,
        "baseline": summary(baseline, 0),
        "candidate": summary(candidate, 1),
        "settings_issues": issues,
        "changes": [key for key in VARIATIONS if left.get(key) != right.get(key)],
        "counts": {key: counts[key] for key in CATEGORIES},
        "paired_evaluable": len(cohorts[0]),
        "paired_compatible": compatible,
        "metrics": rates,
        "action_counts": {
            k: {"baseline": before[k], "candidate": after[k], "delta": after[k] - before[k]}
            for k in ("blocked_attempts", "invalid_requests", "confirmation_required")
        },
        "scenarios": rows,
    }
