"""Shared production-review and replay fixtures."""

from pathlib import Path

import pytest
from pydantic import TypeAdapter

from automated_reviews.json_types import JsonData, JsonObject
from automated_reviews.models import ModelId

type JsonValue = JsonData
type JsonDict = JsonObject

APP_FILE = "src/app.py"
APP_LINES = 12
TEST_FILE = "tests/test_app.py"
TEST_LINES = 8


@pytest.fixture
def checkout(tmp_path: Path, monkeypatch: pytest.MonkeyPatch) -> Path:
    """Create the reviewed checkout used by report boundary tests."""
    root = tmp_path / "checkout"
    (root / "src").mkdir(parents=True)
    (root / "tests").mkdir()
    (root / APP_FILE).write_text("".join(f"line {i}\n" for i in range(1, APP_LINES + 1)))
    (root / TEST_FILE).write_text("".join(f"assert {i}\n" for i in range(1, TEST_LINES + 1)))
    monkeypatch.chdir(root)
    return root


def slop_finding(**overrides: JsonValue) -> JsonDict:
    """Return one grounded slop finding."""
    finding: JsonDict = {
        "tier": "tier1",
        "label": "SLOP",
        "category": "bridge-burning",
        "policy_code": None,
        "location": {"path": APP_FILE, "start_line": 2, "end_line": 4},
        "violated_invariant": "Every error path fails loudly, but this code substitutes a synthetic default on failure",
        "proof_command": "rg '2>/dev/null' src/app.py",
        "pattern": "stderr-suppression-with-fallback",
        "task_narrative": "Fetch the diff and abort on failure",
        "slop_narrative": "Suppressed stderr and returned an empty diff instead",
        "why_it_matters": "masked failure: reviews run on empty input",
        "user_surprise": "review passes although the diff fetch failed",
        "existential_justification": "graceful degradation",
        "failure_mode": "asymmetric-risk-model (#20)",
        "evidence": [{"kind": "diff-snippet", "path": APP_FILE, "lines": [2, 4]}],
    }
    finding.update(overrides)
    return finding


def slop_candidate(**overrides: JsonValue) -> JsonDict:
    """Return one valid slop report candidate."""
    candidate: JsonDict = {
        "schema_version": 1,
        "report_type": "slop",
        "review_scope": [APP_FILE],
        "findings": [slop_finding()],
    }
    candidate.update(overrides)
    return candidate


def pytest_addoption(parser: pytest.Parser) -> None:
    """Declare the model selected outside the reviewer environment."""
    parser.addoption("--replay-model")


@pytest.fixture
def replay_model(pytestconfig: pytest.Config) -> ModelId:
    """Return the required model for a local replay test."""
    model = pytestconfig.getoption("replay_model")
    if not isinstance(model, str) or not model:
        raise pytest.UsageError("--replay-model is required for replay tests")
    return TypeAdapter(ModelId).validate_python(model)
