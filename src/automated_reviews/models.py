"""Validated contracts for frozen review cases."""

from __future__ import annotations

from datetime import datetime
from typing import Annotated, Literal

from pydantic import BaseModel, ConfigDict, Field, PositiveInt, validate_call

GitSha = Annotated[str, Field(pattern=r"^[0-9a-f]{40}$")]
Sha256 = Annotated[str, Field(pattern=r"^[0-9a-f]{64}$")]
ModelId = Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s]+$")]
RepositoryId = Annotated[str, Field(pattern=r"^[^/\s]+/[^/\s]+$")]


class ReplaySpec(BaseModel):
    """All controlled inputs that select one review execution."""

    model_config = ConfigDict(strict=True, frozen=True)

    repository: RepositoryId
    pull_request: PositiveInt
    base_ref: str = Field(min_length=1)
    base_sha: GitSha
    source_head_sha: GitSha
    checkout_sha: GitSha
    infra_sha: GitSha
    report_type: Literal["slop"]
    scope: Literal["diff"]
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
    source_head_sha: GitSha
    checkout_sha: GitSha
    infra_sha: GitSha
    run_id: PositiveInt
    job_id: PositiveInt
    report_type: Literal["slop"]
    scope: Literal["diff"]
    model: ModelId
    opencode_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    runner_image: Literal["ubuntu-24.04"]
    runner_image_version: str = Field(min_length=1)
    runner_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    context_origin: Literal["reconstructed-from-github-state"]
    reviewer_context_sha256: Sha256
    observed_job_log_sha256: Sha256
    observed_review_comments_sha256: Sha256
    captured_at: datetime

    @validate_call
    def replay_spec(self, model: ModelId) -> ReplaySpec:
        """Select a model while preserving every other frozen run input."""
        return ReplaySpec(
            repository=self.repository,
            pull_request=self.pull_request,
            base_ref=self.base_ref,
            base_sha=self.base_sha,
            source_head_sha=self.source_head_sha,
            checkout_sha=self.checkout_sha,
            infra_sha=self.infra_sha,
            report_type=self.report_type,
            scope=self.scope,
            model=model,
        )
