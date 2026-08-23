"""Validated contracts for frozen review cases."""

from __future__ import annotations

from datetime import datetime
from pathlib import Path
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
    runner_base_image: str = Field(pattern=r"^[^\s]+@sha256:[0-9a-f]{64}$")
    local_runner_image_id: str = Field(pattern=r"^sha256:[0-9a-f]{64}$")
    uv_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    just_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    safety_net_version: str = Field(pattern=r"^\d+\.\d+\.\d+$")
    context_origin: Literal["reconstructed-from-github-state"]
    target_bundle_sha256: Sha256
    infra_archive_sha256: Sha256
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


class ReplayResult(BaseModel):
    """Observable result of one local production-review execution."""

    model_config = ConfigDict(strict=True, frozen=True)

    exit_code: int
    output_directory: Path


class OpenCodeReplayConfig(BaseModel):
    """OpenCode configuration installed outside the reviewer repository."""

    model_config = ConfigDict(strict=True, frozen=True, populate_by_name=True)

    schema_url: str = Field(serialization_alias="$schema")
    plugin: tuple[str, ...]
    model: ModelId
    permission: dict[Literal["webfetch"], Literal["deny"]]


class ReplayRunRecord(BaseModel):
    """Machine-readable identity and outcome for one replay."""

    model_config = ConfigDict(strict=True, frozen=True)

    case_id: str
    model: ModelId
    exit_code: int
    local_runner_image_id: str
