"""Command-line interface for review cases and replays."""

import subprocess
from pathlib import Path

from cyclopts import App
from pydantic import validate_call

from automated_reviews.fixtures import load_case
from automated_reviews.models import ModelId

app = App(help="Inspect and replay frozen automated-review environments.")


@app.command
def inspect(case_directory: Path) -> None:
    """Print the validated manifest for one frozen case."""
    case = load_case(case_directory)
    print(case.model_dump_json(indent=2))


@app.command
@validate_call
def dispatch(case_directory: Path, model: ModelId | None = None) -> None:
    """Start one replay on GitHub Actions."""
    case = load_case(case_directory)
    selected_model = case.model if model is None else model
    case.replay_spec(selected_model)
    subprocess.run(
        [
            "gh",
            "workflow",
            "run",
            "replay.yml",
            "--repo",
            "dzackgarza/automated-reviews",
            "--field",
            f"case={case.case_id}",
            "--field",
            f"model={selected_model}",
        ],
        check=True,
    )
    print(f"Dispatched {case.case_id} with {selected_model}")
