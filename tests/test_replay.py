"""Local replays through the frozen production slop reviewer."""

from pathlib import Path

import pytest

from automated_reviews.models import ModelId
from automated_reviews.replay import replay_case

CASE = Path("cases/sage-categories-pr3-run32660872242")


@pytest.mark.replay
def test_sage_categories_pr3_review_runs_in_local_runner(replay_model: ModelId) -> None:
    """The local runner must capture the slop reviewer's observable behavior."""
    result = replay_case(CASE, replay_model)

    assert result.exit_code == 0
    assert (result.output_directory / "model-prompt.md").is_file()
    assert (result.output_directory / "replay.log").is_file()
    assert (result.output_directory / "opencode-live.log").is_file()
    assert (result.output_directory / "opencode.db").is_file()
    assert list((result.output_directory / "candidates").glob("[0-9][0-9][0-9].json"))
