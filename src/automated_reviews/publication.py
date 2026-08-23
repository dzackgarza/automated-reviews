"""Publish downstream workflows from the canonical review source."""

from importlib.resources import files
from pathlib import Path

WORKFLOW_NAMES = ("review-slop.yml", "review-pr.yml")
ISSUE_ALIGNMENT_WORKFLOW = "issue-alignment.yml"
COMPLIANCE_WORKFLOW = "review-compliance.yml"
SUPPORTED_PROFILES = ("python", "bun", "bun-playwright", "bun-python", "docs-and-configs", "rust", "sage")


def workflow_text(name: str, *, profile: str, review_ref: str, qc_ref: str) -> str:
    """Render one downstream workflow with its review and QC owners."""
    assert name in WORKFLOW_NAMES, f"unsupported workflow: {name}"
    assert profile in SUPPORTED_PROFILES, f"unsupported profile: {profile}"
    source_name = "review-pr-bun-playwright.yml" if name == "review-pr.yml" and profile == "bun-playwright" else name
    text = (files("automated_reviews") / "templates" / source_name).read_text(encoding="utf-8")
    return text.replace("{{ review_ref }}", review_ref).replace("{{ profile }}", profile).replace("{{ ref }}", qc_ref)


def issue_alignment_workflow_text(*, review_ref: str) -> str:
    """Render the issue-alignment trigger for a policy-owning repository."""
    text = (files("automated_reviews") / "templates" / ISSUE_ALIGNMENT_WORKFLOW).read_text(encoding="utf-8")
    return text.replace("{{ review_ref }}", review_ref)


def review_labels_text() -> str:
    """Return the canonical labels owned by the review system."""
    return (files("automated_reviews") / "data" / "labels.json").read_text(encoding="utf-8")


def compliance_workflow_text(*, review_ref: str) -> str:
    """Render the policy-compliance trigger."""
    text = (files("automated_reviews") / "templates" / COMPLIANCE_WORKFLOW).read_text(encoding="utf-8")
    return text.replace("{{ review_ref }}", review_ref)


def publish_policy_compliance_workflow(target: Path, *, review_ref: str = "main") -> None:
    """Write the policy-compliance workflow into a target repository."""
    workflow_dir = target / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    output = workflow_dir / COMPLIANCE_WORKFLOW
    assert not output.exists(), f"review workflow already exists: {COMPLIANCE_WORKFLOW}"
    output.write_text(compliance_workflow_text(review_ref=review_ref), encoding="utf-8")


def publish_slop_workflows(
    target: Path,
    *,
    profile: str,
    review_ref: str = "main",
    qc_ref: str = "main",
) -> None:
    """Write the complete downstream slop-review workflow surface."""
    workflow_dir = target / ".github" / "workflows"
    workflow_dir.mkdir(parents=True, exist_ok=True)
    existing = tuple(name for name in WORKFLOW_NAMES if (workflow_dir / name).exists())
    assert not existing, f"review workflows already exist: {', '.join(existing)}"
    for name in WORKFLOW_NAMES:
        (workflow_dir / name).write_text(
            workflow_text(name, profile=profile, review_ref=review_ref, qc_ref=qc_ref),
            encoding="utf-8",
        )
