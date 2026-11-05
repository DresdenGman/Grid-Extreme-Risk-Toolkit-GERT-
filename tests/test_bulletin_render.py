"""Regression tests for bulletin rendering."""

from datetime import datetime

from bulletin.context import build_bulletin_context
from bulletin.render import render_charts, render_html


def test_bulletin_issue_time_shows_actual_minutes():
    # Regression: the issue time was formatted with "%H:%00", which
    # hard-coded the minutes to :00 regardless of the real issue time.
    context = build_bulletin_context()
    context["issued_at"] = datetime(2026, 1, 15, 14, 37)

    html = render_html(context, render_charts(context))

    assert "2026-01-15 14:37" in html
