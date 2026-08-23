"""Validated contracts for frozen review cases."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, validate_call


GitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
ModelId = Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s]+$")]
RepositoryId = Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s]+$")]


class ReplaySpec(BaseModel):
    """All controlled inputs that select one review execution."""

    model_config = ConfigDict(strict=True, frozen=True)

    repository: RepositoryId
    pull_request: PositiveInt
    base_ref: str = Field(min_length=1)
    base_sha: GitSha
    head_sha: GitSha
    infra_sha: GitSha
    model: ModelId


class CaseManifest(BaseModel):
    """Frozen identity and provenance for one observed review run."""

    model_config = ConfigDict(strict=True, frozen=True)

    schema_version: Literal[1]
    case_id: str = Field(pattern=r"^[a-z0-9][a-z0-9-]+$")
    repository: RepositoryId
    pull_request: PositiveInt
    base_ref: str = Field(min_length=1)
    base_sha: GitSha
    head_sha: GitSha
    infra_sha: GitSha
    run_id: PositiveInt
    job_id: PositiveInt
    model: ModelId
    opencode_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    captured_at: datetime

    @validate_call
    def replay_spec(self, model: ModelId) -> ReplaySpec:
        """Select a model while preserving every other frozen run input."""
        return ReplaySpec(
            repository=self.repository,
            pull_request=self.pull_request,
            base_ref=self.base_ref,
            base_sha=self.base_sha,
            head_sha=self.head_sha,
            infra_sha=self.infra_sha,
            model=model,
        )

