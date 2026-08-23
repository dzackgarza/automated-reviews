"""Replay-test command-line inputs."""

import pytest
from pydantic import TypeAdapter

from automated_reviews.models import ModelId


def pytest_addoption(parser: pytest.Parser) -> None:
    """Declare the model selected outside the reviewer environment."""
    parser.addoption("--replay-model")


@pytest.fixture
def replay_model(pytestconfig: pytest.Config) -> ModelId:
    """Return the required model for a local replay test."""
    model = pytestconfig.getoption("replay_model")
    if not isinstance(model, str) or not model:
        raise pytest.UsageError("--replay-model is required for replay tests")
    return TypeAdapter(ModelId).validate_python(model)
