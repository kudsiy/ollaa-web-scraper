"""
The scraper's retry rule (owner, 13 November 2026): a connection drop or timeout is retried
once after a wait; a second failure in a row stops; anything else is never retried. Uses
fake responses only; nothing goes online.
"""
from unittest.mock import MagicMock

import pytest
import requests

from tools import scrape_site


@pytest.fixture
def no_wait(monkeypatch):
    waits = []
    monkeypatch.setattr(scrape_site.time, "sleep", lambda s: waits.append(s))
    return waits


def _fake_get(monkeypatch, outcomes):
    calls = []

    def fake(url, **kwargs):
        calls.append(url)
        outcome = outcomes[len(calls) - 1]
        if isinstance(outcome, Exception):
            raise outcome
        return outcome

    monkeypatch.setattr(scrape_site.requests, "get", fake)
    return calls


def test_connection_drop_is_retried_once(monkeypatch, no_wait):
    page = MagicMock(status_code=200)
    calls = _fake_get(monkeypatch, [requests.exceptions.ConnectionError("reset"), page])
    response, error = scrape_site.fetch_with_one_retry("https://example.invalid/a")
    assert response is page and error is None
    assert len(calls) == 2
    assert no_wait == [scrape_site.RETRY_WAIT]


def test_timeout_is_retried_once(monkeypatch, no_wait):
    page = MagicMock(status_code=200)
    calls = _fake_get(monkeypatch, [requests.exceptions.ReadTimeout("slow"), page])
    response, _ = scrape_site.fetch_with_one_retry("https://example.invalid/b")
    assert response is page and len(calls) == 2


def test_second_failure_in_a_row_stops(monkeypatch, no_wait):
    calls = _fake_get(monkeypatch, [requests.exceptions.ConnectionError("reset"),
                                    requests.exceptions.ReadTimeout("slow")])
    response, error = scrape_site.fetch_with_one_retry("https://example.invalid/c")
    assert response is None and "after one retry" in error
    assert len(calls) == 2


def test_other_errors_are_never_retried(monkeypatch, no_wait):
    calls = _fake_get(monkeypatch, [ValueError("something else")])
    response, error = scrape_site.fetch_with_one_retry("https://example.invalid/d")
    assert response is None and "ValueError" in error
    assert len(calls) == 1 and no_wait == []


def test_a_blocked_page_is_returned_not_retried(monkeypatch, no_wait):
    # A 403 or challenge page is a response, not a connection error: it comes back at once,
    # and the scraper's own check then stops the run without retrying.
    blocked = MagicMock(status_code=403)
    calls = _fake_get(monkeypatch, [blocked])
    response, _ = scrape_site.fetch_with_one_retry("https://example.invalid/e")
    assert response is blocked and len(calls) == 1 and no_wait == []
