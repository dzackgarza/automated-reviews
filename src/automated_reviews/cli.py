"""Command-line interface for review cases and replays."""

from pathlib import Path

from cyclopts import App
from pydantic import validate_call

from automated_reviews.fixtures import load_case
from automated_reviews.models import ModelId
from automated_reviews.replay import replay_case

app = App(help="Inspect and replay frozen automated-review environments.")


@app.command
def inspect(case_directory: Path) -> None:
    """Print the validated manifest for one frozen case."""
    case = load_case(case_directory)
    print(case.model_dump_json(indent=2))


@app.command
@validate_call
def replay(case_directory: Path, model: ModelId | None = None) -> None:
    """Run one frozen case inside the local disposable runner."""
    case = load_case(case_directory)
    selected_model = case.model if model is None else model
    replay_case(case_directory, selected_model)
