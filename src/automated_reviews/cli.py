"""Command-line interface for production reviews and frozen replays."""

from pathlib import Path

from cyclopts import App
from pydantic import validate_call

from automated_reviews.context import fetch_policy_compliance_context, fetch_slop_context
from automated_reviews.fixtures import load_case
from automated_reviews.harness import run_policy_compliance_review, run_slop_review
from automated_reviews.issue_alignment import check_issue_alignment
from automated_reviews.issues import publish_issues
from automated_reviews.metadata import load_review_metadata
from automated_reviews.models import ModelId
from automated_reviews.publication import publish_policy_compliance_workflow, publish_slop_workflows
from automated_reviews.replay import replay_case
from automated_reviews.report import enforce_report_status, report_metadata, report_schema, validate_report
from automated_reviews.sarif import to_sarif
from automated_reviews.threads import post_threads

app = App(help="Run and publish automated slop and policy-compliance reviews.")

app.command(fetch_slop_context)
app.command(fetch_policy_compliance_context)
app.command(run_slop_review)
app.command(run_policy_compliance_review)
app.command(validate_report)
app.command(report_schema)
app.command(report_metadata)
app.command(enforce_report_status)
app.command(to_sarif)
app.command(post_threads)
app.command(publish_issues, name="publish-issues")
app.command(check_issue_alignment, name="check-issue-alignment")
app.command(publish_slop_workflows)
app.command(publish_policy_compliance_workflow)


@app.command
def active_model() -> None:
    """Print the active production slop-review model."""
    print(load_review_metadata().model)


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
