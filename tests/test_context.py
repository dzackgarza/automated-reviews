"""Reviewer context rendering for captured GitHub alert shapes."""

import pytest

from automated_reviews.context import (
    _format_alert,
    _thread_digest,
    _validated_alert_page,
)
from automated_reviews.json_types import JsonObject


def _alert(number: int, state: str, label: str, path: str, line: int) -> JsonObject:
    return {
        "number": number,
        "state": state,
        "html_url": f"https://github.com/owner/repo/security/code-scanning/{number}",
        "rule": {"id": label.lower().replace(" ", "-"), "name": label},
        "most_recent_instance": {"location": {"path": path, "start_line": line}},
    }


def test_alert_format_uses_github_rule_name_without_location_properties() -> None:
    alert = {
        "html_url": "https://github.com/owner/repo/security/code-scanning/1",
        "rule": {"id": "bridge-burning", "name": "Bridge Burning"},
        "most_recent_instance": {"location": {"path": "src/app.py", "start_line": 7}},
    }

    assert _format_alert(alert) == "- **Bridge Burning** at `src/app.py:7`  \n  Alert: https://github.com/owner/repo/security/code-scanning/1"


def test_alert_format_uses_github_rule_id_when_name_is_absent() -> None:
    alert = {
        "html_url": "https://github.com/owner/repo/security/code-scanning/2",
        "rule": {"id": "bridge-burning"},
        "most_recent_instance": {"location": {"path": "src/app.py", "start_line": 8}},
    }

    assert _format_alert(alert) == "- **bridge-burning** at `src/app.py:8`  \n  Alert: https://github.com/owner/repo/security/code-scanning/2"


def test_alert_format_rejects_missing_rule_name_and_id() -> None:
    alert = {
        "html_url": "https://github.com/owner/repo/security/code-scanning/3",
        "rule": {},
        "most_recent_instance": {"location": {"path": "src/app.py", "start_line": 9}},
    }

    with pytest.raises(SystemExit):
        _format_alert(alert)


def test_alert_format_rejects_invalid_rule_and_location_shapes() -> None:
    empty_rule_id = {
        "html_url": "https://github.com/owner/repo/security/code-scanning/4",
        "rule": {"id": ""},
        "most_recent_instance": {"location": {"path": "src/app.py", "start_line": 10}},
    }
    string_line = {
        "html_url": "https://github.com/owner/repo/security/code-scanning/5",
        "rule": {"id": "bridge-burning"},
        "most_recent_instance": {"location": {"path": "src/app.py", "start_line": "10"}},
    }

    with pytest.raises(SystemExit):
        _format_alert(empty_rule_id)
    with pytest.raises(SystemExit):
        _format_alert(string_line)


def test_alert_page_validation_rejects_invalid_payload_shapes() -> None:
    with pytest.raises(SystemExit):
        _validated_alert_page("{}", "repos/owner/repo/code-scanning/alerts")
    with pytest.raises(SystemExit):
        _validated_alert_page('["not an alert object"]', "repos/owner/repo/code-scanning/alerts")


def test_thread_digest_uses_review_thread_path() -> None:
    node = {
        "path": "src/ai_review_ci/context.py",
        "isResolved": False,
        "comments": {
            "nodes": [
                {
                    "body": "### Finding headline\n\nFinding body.",
                }
            ]
        },
    }

    assert _thread_digest(node) == {
        "path": "src/ai_review_ci/context.py",
        "headline": "### Finding headline",
        "resolved": False,
    }


def test_thread_digest_skips_threads_without_comments() -> None:
    node = {
        "path": "src/ai_review_ci/context.py",
        "isResolved": True,
        "comments": {"nodes": []},
    }

    assert _thread_digest(node) is None
