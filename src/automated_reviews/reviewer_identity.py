"""Shared reviewer identity metadata for PR threads and SARIF results."""

from automated_reviews.metadata import load_review_metadata

JsonDict = dict[str, str]

REVIEW_AGENT = "opencode-ai"
REVIEW_PROMPT_VERSION = "1.0.0"


def reviewer_identity(report_type: str) -> JsonDict:
    """Structured reviewer identity used by every review publication surface."""
    return {
        "type": report_type,
        "agent": REVIEW_AGENT,
        "prompt_id": f"reviews/{report_type}",
        "prompt_version": REVIEW_PROMPT_VERSION,
        "model": load_review_metadata().model,
    }
