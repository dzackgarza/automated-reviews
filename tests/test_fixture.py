from pathlib import Path

from automated_reviews.fixtures import load_case
from automated_reviews.models import ReplaySpec

CASE = Path("cases/sage-categories-pr3-run32660872242")


def test_pr3_case_builds_the_original_replay_specification() -> None:
    """The frozen case must select the exact source and review infrastructure."""
    case = load_case(CASE)

    assert case.replay_spec("opencode/nemotron-3-ultra-free") == ReplaySpec(
        repository="dzackgarza/sage-categories",
        pull_request=3,
        base_ref="main",
        base_sha="6d91a14b704135c06906043ae0f83da529d0448f",
        source_head_sha="7566eb20b1d996c92d63ac0dee371ddd8aee6e2b",
        checkout_sha="c84f1a080a03c34a537edf92e86331823d39239b",
        infra_sha="c63800d106abab8e664daab4121d6d62a5bc6e71",
        report_type="slop",
        scope="diff",
        model="opencode/nemotron-3-ultra-free",
    )

    assert case.reviewer_context_sha256 == "bb2e60044ca827f0e063a427a9d1b1c42132bb810f2313801febdbf9c7bad544"
    assert case.observed_job_log_sha256 == "b4c2f7d907e59c9391faae2d3e257cace1263560d9eaab355508fc9844c7b949"
