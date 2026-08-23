"""Canonical metadata for production LLM reviews."""

import tomllib
from importlib.resources import files
from typing import Literal

from pydantic import BaseModel, ConfigDict, Field


class ReviewMetadata(BaseModel):
    """Versioned production reviewer selection."""

    model_config = ConfigDict(extra="forbid", frozen=True)

    schema_version: Literal[1]
    model: str = Field(pattern=r"^[a-z0-9][a-z0-9-]*/[A-Za-z0-9][A-Za-z0-9._-]*$")


def parse_review_metadata(text: str) -> ReviewMetadata:
    """Validate reviewer metadata from TOML text."""
    return ReviewMetadata.model_validate(tomllib.loads(text))


def load_review_metadata() -> ReviewMetadata:
    """Load the tracked production reviewer metadata."""
    source = files("automated_reviews") / "data" / "reviewer.toml"
    return parse_review_metadata(source.read_text(encoding="utf-8"))
