"""Command-line interface for review cases and replays."""

from pathlib import Path

from cyclopts import App

from automated_reviews.fixtures import load_case


app = App(help="Inspect and replay frozen automated-review environments.")


@app.command
def inspect(case_directory: Path) -> None:
    """Print the validated manifest for one frozen case."""
    case = load_case(case_directory)
    print(case.model_dump_json(indent=2))

