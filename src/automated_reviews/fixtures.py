"""Load frozen review cases from their canonical TOML manifests."""

from __future__ import annotations

import tomllib
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
