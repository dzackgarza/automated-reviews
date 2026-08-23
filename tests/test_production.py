from pathlib import Path

from automated_reviews.harness import OpencodeConfig, opencode_command
from automated_reviews.metadata import load_review_metadata
from automated_reviews.publication import workflow_text


def test_active_model_controls_opencode_invocation() -> None:
    metadata = load_review_metadata()
    config = OpencodeConfig(
        binary=Path("/usr/local/bin/opencode"),
        timeout=600,
        max_attempts=5,
        backoff=5,
        model=metadata.model,
    )

    assert metadata.model == "opencode-go/ox-alpha-free"
    assert opencode_command(config, 1) == [
        "/usr/local/bin/opencode",
        "run",
        "--model",
        metadata.model,
    ]


def test_published_pr_workflow_uses_each_canonical_owner() -> None:
    text = workflow_text("review-pr.yml", profile="python", review_ref="main", qc_ref="main")

    assert "dzackgarza/automated-reviews/.github/workflows/_review.yml@main" in text
    assert "dzackgarza/ai-review-ci/.github/workflows/_qc.yml@main" in text


def test_published_slop_workflow_uses_automated_reviews() -> None:
    text = workflow_text("review-slop.yml", profile="python", review_ref="release/v2", qc_ref="main")

    assert "dzackgarza/automated-reviews/.github/workflows/_review.yml@release/v2" in text
