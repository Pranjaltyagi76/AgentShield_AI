from copy import deepcopy
from types import SimpleNamespace
from uuid import uuid4

import pytest

from app.comparison import compare_runs


def fixture(outcomes):
    entries = []
    results = []
    for sid, outcome in outcomes.items():
        entries.append({"id": sid, "version": 2, "context": {"available_tools": ["a", "b"]}})
        assessment = {
            "outcome": outcome,
            "adversarial": True,
            "action_applicable": True,
            "disclosure_applicable": False,
            "benign_applicable": False,
            "unsafe_objective": outcome == "fail",
            "disclosed": False,
            "benign_completed": False,
            "contained": outcome == "pass",
            "counts": {},
            "reason": None,
            "findings": [],
        }
        results.append(
            SimpleNamespace(
                scenario_id=sid,
                scenario_version=2,
                status="completed" if outcome != "inconclusive" else "cancelled",
                started_at=1,
                reason=None,
                assessment=assessment,
                outcome=outcome,
            )
        )
    config = {
        "oracle_version": "1",
        "runtime_version": "2",
        "tool_schema_hash": "abc",
        "policy": {"version": "1", "max_calls": 6},
        "limits": {"steps": 10, "calls": 6, "total_bytes": 20000, "run_seconds": 180},
        "provider": "demo",
        "model": "scripted",
        "tools": ["a", "b"],
        "profile": "hardened",
        "behavior_version": "2",
        "prompt_hash": "first",
        "scenarios": entries,
        "confirmation": None,
    }
    return SimpleNamespace(
        id=uuid4(), version_id=uuid4(), status="completed", config=config
    ), results


def test_common_cohort_and_coverage_use_distinct_denominators():
    a, ar = fixture(
        {
            "AS-001": "fail",
            "AS-002": "pass",
            "AS-003": "pass",
            "AS-004": "pass",
            "AS-005": "pass",
            "AS-006": "pass",
        }
    )
    b, br = fixture(
        {
            "AS-001": "pass",
            "AS-002": "fail",
            "AS-003": "pass",
            "AS-004": "inconclusive",
            "AS-005": "fail",
            "AS-007": "fail",
        }
    )
    b.config["scenarios"][4]["version"] = br[4].scenario_version = 3
    b.config["scenarios"].reverse()
    report = compare_runs(a, b, ar, br)
    assert report["counts"] == {
        "improved": 1,
        "regressed": 1,
        "unchanged": 1,
        "inconclusive": 1,
        "incompatible": 1,
        "unmatched": 2,
    }
    assert report["metrics"]["pass_rate"]["baseline"]["numerator"] == 2
    assert report["metrics"]["pass_rate"]["candidate"]["denominator"] == 3
    assert report["metrics"]["pass_rate"]["delta_pp"] == 0
    assert report["metrics"]["coverage"]["delta_pp"] == -25
    assert report["candidate"]["coverage"]["denominator"] == 6
    assert report["metrics"]["secret_exposure"]["delta_pp"] is None


@pytest.mark.parametrize(
    "setting",
    ["oracle_version", "runtime_version", "tool_schema_hash", "policy", "limits", "model", "tools"],
)
def test_mismatched_configuration_cannot_be_an_improvement(setting):
    a, ar = fixture({"AS-001": "fail"})
    b, br = fixture({"AS-001": "pass"})
    b.config[setting] = ["new_tool"] if setting == "tools" else "different"
    report = compare_runs(a, b, ar, br)
    assert report["scenarios"][0]["issues"] == [setting]
    assert report["paired_evaluable"] == 0
    assert report["metrics"]["pass_rate"]["delta_pp"] is None


def test_prompt_changes_and_reordered_tool_sets_are_compatible():
    a, ar = fixture({"AS-011": "pass"})
    b = deepcopy(a)
    b.config["prompt_hash"] = "edited"
    b.config["tools"].reverse()
    b.config["scenarios"][0]["context"]["available_tools"].reverse()
    report = compare_runs(a, b, ar, ar)
    assert report["counts"]["unchanged"] == 1
    assert report["changes"] == ["prompt_hash"]


def test_approval_only_affects_target_scenario_and_missing_provenance_fails_closed():
    a, ar = fixture({"AS-006": "fail", "AS-011": "pass"})
    b, br = fixture({"AS-006": "pass", "AS-011": "pass"})
    b.config["confirmation"] = {"scenario": "AS-006", "step": 1}
    report = compare_runs(a, b, ar, br)
    assert report["scenarios"][0]["issues"] == ["confirmation"]
    assert report["paired_evaluable"] == 1
    b.config.pop("oracle_version")
    assert "missing_oracle_version" in compare_runs(a, b, ar, br)["settings_issues"]


def test_fixture_context_change_excludes_only_affected_case():
    a, ar = fixture({"AS-001": "fail", "AS-011": "fail"})
    b, br = fixture({"AS-001": "pass", "AS-011": "pass"})
    b.config["scenarios"][0]["context"]["available_tools"] = ["b"]
    report = compare_runs(a, b, ar, br)
    assert report["scenarios"][0]["issues"] == ["scenario_context"]
    assert report["paired_evaluable"] == 1 and report["counts"]["improved"] == 1


def test_legacy_runs_with_empty_policy_and_limits_cannot_be_scored():
    a, ar = fixture({"AS-001": "fail"})
    b, br = fixture({"AS-001": "pass"})
    for cfg in (a.config, b.config):
        cfg.update(policy={}, limits={})
    report = compare_runs(a, b, ar, br)
    assert report["settings_issues"] == ["missing_policy", "missing_limits"]
    assert report["metrics"]["pass_rate"]["delta_pp"] is None


def test_missing_evidence_is_inconclusive_even_with_a_recorded_outcome():
    a, ar = fixture({"AS-011": "pass"})
    b, br = fixture({"AS-011": "fail"})
    br[0].assessment = None
    for rows in (br, []):
        report = compare_runs(a, b, ar, rows)
        assert report["counts"]["inconclusive"] == 1
        assert report["metrics"]["coverage"]["delta_pp"] == -100
        assert report["metrics"]["pass_rate"]["delta_pp"] is None
