"""Load frozen review cases from their canonical TOML manifests."""

from __future__ import annotations

import tomllib
from hashlib import file_digest
from pathlib import Path

from pydantic import validate_call

from automated_reviews.models import CaseManifest


@validate_call
def load_case(case_directory: Path) -> CaseManifest:
    """Load and validate one case manifest."""
    manifest_path = case_directory / "case.toml"
    with manifest_path.open("rb") as manifest_file:
        manifest_data = tomllib.load(manifest_file)
    return CaseManifest.model_validate(manifest_data)


@validate_call
def verify_case_artifacts(case_directory: Path) -> None:
    """Verify every committed byte stream used by a replay."""
    case = load_case(case_directory)
    expected = (
        ("target.bundle", case.target_bundle_sha256),
        ("infra.tar.gz", case.infra_archive_sha256),
        ("reviewer-context.txt", case.reviewer_context_sha256),
        ("observed-job.log", case.observed_job_log_sha256),
        ("observed-review-comments.json", case.observed_review_comments_sha256),
    )
    for filename, digest in expected:
        with (case_directory / filename).open("rb") as artifact:
            observed = file_digest(artifact, "sha256").hexdigest()
        if observed != digest:
            raise ValueError(f"digest mismatch for {filename}: {observed}")
