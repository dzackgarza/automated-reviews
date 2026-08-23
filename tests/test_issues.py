"""Tests for the issues-ledger delivery path (publish-issues + context)."""

import json
from pathlib import Path

import yaml

from automated_reviews.context import _issue_ledger_lines
from automated_reviews.issues import (
    FINGERPRINT_MARKER,
    _issue_body,
    _marked_fingerprint,
    issue_fingerprint,
)
from automated_reviews.json_types import JsonObject
from automated_reviews.policy_index import canonical_route, load_policy_index

ROOT = Path(__file__).parent.parent

JsonDict = JsonObject


def _finding(label: str = "WRONG_DUAL", path: str = "src/lattice.py") -> JsonDict:
    return {
        "label": label,
        "tier": "tier1",
        "category": "semantic-regression",
        "location": {"path": path, "start_line": 10, "end_line": 12},
        "violated_invariant": "dual() must rescale the form",
        "proof_command": "grep -n 'def dual' src/lattice.py",
    }


def _artifact(tmp_path: Path, findings: list[JsonDict]) -> Path:
    artifact = tmp_path / ".review-report-artifact.json"
    artifact.write_text(json.dumps({"report_type": "slop", "findings": findings}))
    return artifact


def test_issue_fingerprint_is_finer_than_coarse_fingerprint() -> None:
    # Two distinct invariants in the same file and category must be two
    # tracked issues, not one.
    a = issue_fingerprint("semantic-regression", "src/lattice.py", "WRONG_DUAL")
    b = issue_fingerprint("semantic-regression", "src/lattice.py", "WRONG_SATURATION")
    assert a != b
    assert a == issue_fingerprint("semantic-regression", "src/lattice.py", "WRONG_DUAL")


def test_issue_body_carries_marker_narrative_and_parent() -> None:
    body = _issue_body(_finding(), "slop", parent_issue=46, sha="abc123")
    fp = issue_fingerprint("semantic-regression", "src/lattice.py", "WRONG_DUAL")
    assert _marked_fingerprint(body) == fp
    assert "src/lattice.py:10-12" in body
    assert "dual() must rescale the form" in body
    assert "grep -n 'def dual' src/lattice.py" in body
    assert "Tracked under #46." in body
    assert "do-not-re-raise" in body


def test_issue_body_routes_to_catalogue_without_inlining_remediation() -> None:
    finding = _finding()
    finding["policy_code"] = "POLICY.NO_HIDDEN_CONFIG"

    body = _issue_body(finding, "slop", parent_issue=46, sha="abc123")

    route = canonical_route("POLICY.NO_HIDDEN_CONFIG")
    remediation_text = load_policy_index().remediation_for_policy("POLICY.NO_HIDDEN_CONFIG").required_remediation
    assert f"`{route.policy_code}` → `{route.remediation_code}`" in body
    assert remediation_text not in body


def test_marked_fingerprint_ignores_unmarked_bodies() -> None:
    assert _marked_fingerprint("just prose, no marker") is None
    assert _marked_fingerprint(f"<!-- {FINGERPRINT_MARKER} abc123 -->\nrest") == "abc123"


def test_context_issue_ledger_lines_render_states() -> None:
    lines = _issue_ledger_lines(
        "ai-review/slop",
        [
            {"number": 7, "state": "open", "title": "open finding"},
            {"number": 3, "state": "closed", "state_reason": "not_planned", "title": "rejected finding"},
        ],
    )
    text = "\n".join(lines)
    assert "do not re-report" in text
    assert "open finding (#7)" in text
    assert "rejected finding (#3, not_planned)" in text
    assert "do not re-raise" in text
    assert _issue_ledger_lines("ai-review/slop", []) == []


def test_slop_review_workflow_gates_delivery_paths() -> None:
    workflow = yaml.safe_load((ROOT / ".github" / "workflows" / "_slop-review.yml").read_text())
    inputs = workflow[True]["workflow_call"]["inputs"]
    assert inputs["delivery"]["default"] == "sarif"
    assert inputs["parent_issue"]["type"] == "number"

    steps = workflow["jobs"]["slop-review"]["steps"]
    by_name = {step.get("name"): step for step in steps}
    assert by_name["Convert report to SARIF"]["if"] == "inputs.delivery == 'sarif'"
    assert by_name["Upload slop findings"]["if"] == "inputs.delivery == 'sarif'"
    publish = by_name["Publish findings to the issues ledger"]
    assert publish["if"] == "inputs.delivery == 'issues'"
    assert "publish-issues" in publish["run"]
    assert workflow["jobs"]["slop-review"]["permissions"]["issues"] == "write"
