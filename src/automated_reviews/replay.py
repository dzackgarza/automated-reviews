"""Run a frozen production reviewer inside a local disposable runner."""

from __future__ import annotations

import subprocess
import sys
from pathlib import Path
from threading import Thread
from typing import BinaryIO
from uuid import uuid4

from pydantic import validate_call

from automated_reviews.fixtures import load_case, verify_case_artifacts
from automated_reviews.models import (
    ModelId,
    OpenCodeReplayConfig,
    ReplayResult,
    ReplayRunRecord,
)

RUNNER_DIRECTORY = Path("environments/github-ubuntu-24.04")
ARTIFACT_DIRECTORY = Path(".git/automated-reviews/artifacts")
CONTROL_REPO = "/home/runner/work/sage-categories/sage-categories"
INFRA_REPO = "/home/runner/work/_temp/ai-review-ci"
PRIVATE_SUBMIT = "/opt/ai-review/private/ci/private/submit-candidate"


def _run(command: list[str], *, capture_output: bool = False) -> subprocess.CompletedProcess[str]:
    """Run one host command and fail on an unexpected status."""
    return subprocess.run(command, check=True, capture_output=capture_output, text=True)


def _container_exec(container_id: str, command: list[str]) -> subprocess.CompletedProcess[str]:
    """Run one setup command in the local runner."""
    return _run(["docker", "container", "exec", container_id, *command])


def _stream_review(container_id: str, command: list[str], log_path: Path) -> int:
    """Stream the model transcript to the terminal and its replay artifact."""
    activity_path = log_path.with_name("opencode-live.log")
    activity = subprocess.Popen(
        [
            "docker",
            "container",
            "exec",
            container_id,
            "tail",
            "--follow=name",
            "--retry",
            "/home/reviewer/.local/share/opencode/log/opencode.log",
        ],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    process = subprocess.Popen(
        ["docker", "container", "exec", container_id, *command],
        stdout=subprocess.PIPE,
        stderr=subprocess.STDOUT,
    )
    assert process.stdout is not None
    assert activity.stdout is not None
    with log_path.open("wb") as log_file, activity_path.open("wb") as activity_file:
        observer = Thread(target=_copy_stream, args=(activity.stdout, activity_file), daemon=True)
        observer.start()
        while chunk := process.stdout.read(4096):
            log_file.write(chunk)
            sys.stdout.buffer.write(chunk)
            sys.stdout.buffer.flush()
        exit_code = process.wait()
        activity.terminate()
        activity.wait()
        observer.join()
    return exit_code


def _copy_stream(source: BinaryIO, destination: BinaryIO) -> None:
    """Copy local runner activity to its durable observation stream."""
    while chunk := source.read(4096):
        destination.write(chunk)
        destination.flush()
        sys.stdout.buffer.write(chunk)
        sys.stdout.buffer.flush()


def _copy_from_container(container_id: str, source: str, destination: Path) -> None:
    """Copy one observed runner artifact to the host."""
    _run(["docker", "container", "cp", f"{container_id}:{source}", str(destination)])


def _container_path_exists(container_id: str, path: str) -> bool:
    """Test one optional output path after the reviewer exits."""
    result = subprocess.run(
        ["docker", "container", "exec", container_id, "test", "-e", path],
        check=False,
    )
    return result.returncode == 0


def _frozen_runner(case_directory: Path) -> str:
    """Return the local runner only when its content matches the fixture."""
    case = load_case(case_directory)
    image_tag = f"automated-reviews/{case.case_id}:runner"
    inspection = subprocess.run(
        ["docker", "image", "inspect", image_tag, "--format", "{{.Id}}"],
        check=False,
        capture_output=True,
        text=True,
    )
    if inspection.returncode != 0:
        _run(["docker", "build", "--tag", image_tag, str(RUNNER_DIRECTORY)])
        inspection = _run(
            ["docker", "image", "inspect", image_tag, "--format", "{{.Id}}"],
            capture_output=True,
        )
    image_id = inspection.stdout.strip()
    if image_id != case.local_runner_image_id:
        raise RuntimeError(f"local runner image is {image_id}; fixture requires {case.local_runner_image_id}")
    return image_tag


def _create_runner(case_directory: Path, output_directory: Path, image_tag: str) -> str:
    """Create one runner with only frozen inputs and an external capture mount."""
    case_mount = f"{case_directory.resolve()}:/fixtures:ro"
    capture_mount = f"{RUNNER_DIRECTORY.resolve()}:/capture:ro"
    output_mount = f"{output_directory.resolve()}:/replay-output:rw"
    result = _run(
        [
            "docker",
            "container",
            "create",
            "--env",
            f"GITHUB_WORKSPACE={CONTROL_REPO}",
            "--env",
            "GITHUB_REPOSITORY=dzackgarza/sage-categories",
            "--env",
            "RUNNER_TEMP=/home/runner/work/_temp",
            "--volume",
            case_mount,
            "--volume",
            capture_mount,
            "--volume",
            output_mount,
            image_tag,
        ],
        capture_output=True,
    )
    container_id = result.stdout.strip()
    if not container_id:
        raise RuntimeError("docker did not return a container identifier")
    _run(["docker", "container", "start", container_id])
    return container_id


def _materialize_case(container_id: str, case_directory: Path) -> None:
    """Materialize the exact checkout, infrastructure, and reviewer context."""
    case = load_case(case_directory)
    _container_exec(
        container_id,
        ["mkdir", "-p", CONTROL_REPO, INFRA_REPO, "/replay-output/candidates"],
    )
    _container_exec(
        container_id,
        ["git", "clone", "--no-checkout", "/fixtures/target.bundle", CONTROL_REPO],
    )
    _container_exec(
        container_id,
        [
            "git",
            "-C",
            CONTROL_REPO,
            "update-ref",
            "--no-deref",
            "HEAD",
            case.checkout_sha,
        ],
    )
    _container_exec(container_id, ["git", "-C", CONTROL_REPO, "read-tree", "HEAD"])
    _container_exec(container_id, ["git", "-C", CONTROL_REPO, "checkout-index", "--all"])
    _container_exec(
        container_id,
        [
            "git",
            "-C",
            CONTROL_REPO,
            "update-ref",
            f"refs/remotes/origin/{case.base_ref}",
            case.base_sha,
        ],
    )
    _container_exec(container_id, ["tar", "-xzf", "/fixtures/infra.tar.gz", "-C", INFRA_REPO])
    _container_exec(
        container_id,
        [
            "cp",
            "/fixtures/reviewer-context.txt",
            f"{CONTROL_REPO}/.reviewer-context.md",
        ],
    )


def _prepare_reviewer(container_id: str, case_directory: Path, model: ModelId, output_directory: Path) -> None:
    """Run production preparation, then install invisible capture and model controls."""
    case = load_case(case_directory)
    runner_just = f"{INFRA_REPO}/ci/runner.just"
    _container_exec(container_id, ["just", "-f", runner_just, "prepare"])
    _container_exec(container_id, ["mv", PRIVATE_SUBMIT, f"{PRIVATE_SUBMIT}.real"])
    _container_exec(
        container_id,
        ["install", "-m", "0500", "/capture/capture-submit", PRIVATE_SUBMIT],
    )

    config = OpenCodeReplayConfig(
        schema_url="https://opencode.ai/config.json",
        plugin=(f"cc-safety-net@{case.safety_net_version}",),
        model=model,
        permission={"webfetch": "deny"},
    )
    config_path = output_directory / "opencode.json"
    config_path.write_text(config.model_dump_json(by_alias=True, indent=2) + "\n")
    _container_exec(
        container_id,
        [
            "install",
            "-o",
            "reviewer",
            "-g",
            "reviewer",
            "-m",
            "0644",
            "/replay-output/opencode.json",
            "/home/reviewer/.config/opencode/opencode.json",
        ],
    )
    _container_exec(container_id, ["just", "-f", runner_just, "check-reviewer-model"])
    _container_exec(container_id, ["just", "-f", runner_just, "stage-pr-diff", case.base_ref])


def _capture_outputs(container_id: str, output_directory: Path) -> None:
    """Copy model-visible input, session state, and final output to the host."""
    required = {
        "/home/reviewer/repo/.agents/review-runner/task.md": output_directory / "model-prompt.md",
    }
    for source, destination in required.items():
        _copy_from_container(container_id, source, destination)

    optional = {
        f"{CONTROL_REPO}/.agents/review-runner/candidates/submitted.json": output_directory / "submitted.json",
        f"{CONTROL_REPO}/.review-report-artifact.json": output_directory / "report.json",
        "/home/reviewer/.local/share/opencode/opencode.db": output_directory / "opencode.db",
        "/home/reviewer/.local/share/opencode/opencode.db-wal": output_directory / "opencode.db-wal",
        "/home/reviewer/.local/share/opencode/opencode.db-shm": output_directory / "opencode.db-shm",
        "/home/reviewer/.local/share/opencode/log": output_directory / "opencode-log",
    }
    for source, destination in optional.items():
        if _container_path_exists(container_id, source):
            _copy_from_container(container_id, source, destination)


@validate_call
def replay_case(case_directory: Path, model: ModelId) -> ReplayResult:
    """Run one model against a frozen case in the local disposable runner."""
    verify_case_artifacts(case_directory)
    case = load_case(case_directory)
    model_directory = model.replace("/", "--")
    output_directory = ARTIFACT_DIRECTORY / case.case_id / model_directory / uuid4().hex
    output_directory.mkdir(parents=True)
    image_tag = _frozen_runner(case_directory)
    container_id = _create_runner(case_directory, output_directory, image_tag)
    exit_code = 1
    try:
        _materialize_case(container_id, case_directory)
        _prepare_reviewer(container_id, case_directory, model, output_directory)
        exit_code = _stream_review(
            container_id,
            [
                "just",
                "-f",
                f"{INFRA_REPO}/ci/runner.just",
                "run-review",
                case.report_type,
                case.scope,
            ],
            output_directory / "replay.log",
        )
        _capture_outputs(container_id, output_directory)
    finally:
        _run(["docker", "container", "stop", container_id])
        _run(["docker", "container", "remove", container_id])

    record = ReplayRunRecord(
        case_id=case.case_id,
        model=model,
        exit_code=exit_code,
        local_runner_image_id=case.local_runner_image_id,
    )
    (output_directory / "run.json").write_text(record.model_dump_json(indent=2) + "\n")
    print(f"Replay artifacts: {output_directory}")
    return ReplayResult(exit_code=exit_code, output_directory=output_directory)
