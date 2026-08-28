from pathlib import Path

from automated_reviews.harness import OpencodeConfig, opencode_command
from automated_reviews.metadata import load_review_metadata
from automated_reviews.policy_index import skills_path
from automated_reviews.publication import compliance_workflow_text, review_labels_text, workflow_text


def test_active_model_controls_opencode_invocation() -> None:
    metadata = load_review_metadata()
    config = OpencodeConfig(
        binary=Path("/usr/local/bin/opencode"),
        timeout=600,
        max_attempts=5,
        backoff=5,
        model=metadata.model,
    )

    assert metadata.model == "opencode/nemotron-3-ultra-free"
    assert opencode_command(config, 1) == [
        "/usr/local/bin/opencode",
        "run",
        "--model",
        metadata.model,
    ]


def test_published_pr_workflow_uses_each_canonical_owner() -> None:
    text = workflow_text("review-pr.yml", profile="python", review_ref="main", qc_ref="main")

    assert "dzackgarza/automated-reviews/.github/workflows/_slop-review.yml@main" in text
    assert "dzackgarza/ai-review-ci/.github/workflows/_qc.yml@main" in text


def test_published_slop_workflow_uses_automated_reviews() -> None:
    text = workflow_text("review-slop.yml", profile="python", review_ref="release/v2", qc_ref="main")

    assert "dzackgarza/automated-reviews/.github/workflows/_slop-review.yml@release/v2" in text


def test_published_compliance_workflow_consumes_contributing() -> None:
    text = compliance_workflow_text(review_ref="release/v2")

    assert "name: Policy Compliance Review" in text
    assert "dzackgarza/automated-reviews/.github/workflows/_policy-compliance-review.yml@release/v2" in text
    assert "policy_document: CONTRIBUTING.md" in text


def test_review_policy_and_labels_are_published_package_data() -> None:
    assert (skills_path() / "policy-index" / "references" / "policies.md").is_file()
    assert "needs-alignment-ruling" in review_labels_text()
