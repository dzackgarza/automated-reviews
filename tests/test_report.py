import json
import pathlib

import pytest

from automated_reviews.report import enforce_report_status, report_metadata, validate_report
from automated_reviews.report_models import finding_fingerprint
from tests.conftest import APP_FILE, slop_candidate, slop_finding


def test_report_metadata_emits_structured_findings(tmp_path: pathlib.Path, checkout: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    artifact = tmp_path / "artifact.json"
    artifact.write_text(json.dumps(slop_candidate(findings=[slop_finding()])))

    report_metadata(artifact)

    payload = json.loads(capsys.readouterr().out)
    assert payload["report_type"] == "slop"
    assert payload["finding_count"] == 1
    assert payload["tier1_count"] == 1
    assert payload["findings"] == [
        {
            "fingerprint": finding_fingerprint("bridge-burning", APP_FILE),
            "tier": "tier1",
            "type": "slop",
            "category": "bridge-burning",
            "label": "SLOP",
            "path": APP_FILE,
            "line": 2,
            "end_line": 4,
            "status": "open",
        }
    ]


def test_enforce_report_status_reports_tier1_without_blocking(tmp_path: pathlib.Path, checkout: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    tier1 = tmp_path / "tier1.json"
    tier1.write_text(json.dumps(slop_candidate(findings=[slop_finding(tier="tier1")])))
    tier2 = tmp_path / "tier2.json"
    tier2.write_text(json.dumps(slop_candidate(findings=[slop_finding(tier="tier2", category="docs")])))

    enforce_report_status(tier1)
    assert "thread-resolution owns PR blocking" in capsys.readouterr().err

    enforce_report_status(tier2)


def test_empty_report_metadata_and_status(tmp_path: pathlib.Path, checkout: pathlib.Path, capsys: pytest.CaptureFixture[str]) -> None:
    # An honest empty report flows through metadata and status enforcement
    # without inventing findings and without failing the run.
    artifact = tmp_path / "empty.json"
    artifact.write_text(json.dumps(slop_candidate(findings=[])))

    report_metadata(artifact)
    payload = json.loads(capsys.readouterr().out)
    assert payload["finding_count"] == 0
    assert payload["tier1_count"] == 0
    assert payload["findings"] == []

    enforce_report_status(artifact)


def test_compliance_validation_reads_allowed_ids_from_policy_document(tmp_path: pathlib.Path, checkout: pathlib.Path) -> None:
    policy = tmp_path / "CONTRIBUTING.md"
    policy.write_text("| `POL-CAT-001` | Categories own constructors. |\n")
    candidate = tmp_path / "candidate.json"
    candidate.write_text(
        json.dumps(
            {
                "review_scope": [APP_FILE],
                "findings": [
                    {
                        "tier": "tier1",
                        "label": "POLICY VIOLATION",
                        "category": "category-ownership",
                        "policy_code": "POL-CAT-001",
                        "location": {"path": APP_FILE, "start_line": 2, "end_line": 4},
                        "violated_policy": "A category owns its constructors and implementation types.",
                        "observed_behavior": "The object class constructs category-owned arrows directly.",
                        "consequence": "The public owner differs from the policy owner.",
                        "evidence": [{"kind": "file-read", "path": APP_FILE, "lines": [2, 4]}],
                    }
                ],
            }
        )
    )
    artifact = tmp_path / "artifact.json"

    validate_report(candidate, "compliance", artifact, policy)

    assert json.loads(artifact.read_text())["findings"][0]["policy_code"] == "POL-CAT-001"
