from datetime import UTC, date, datetime

from app.models.enums import AlertKind
from app.services.alerts import alert_triggered
from app.services.calendar import event_in_window, events_from_extra, should_calendar_push


def test_alert_below_and_above() -> None:
    assert alert_triggered(AlertKind.BELOW, 100, price=99, change_pct=None) is True
    assert alert_triggered(AlertKind.BELOW, 100, price=100, change_pct=None) is True
    assert alert_triggered(AlertKind.BELOW, 100, price=101, change_pct=None) is False
    assert alert_triggered(AlertKind.ABOVE, 200, price=200, change_pct=None) is True
    assert alert_triggered(AlertKind.ABOVE, 200, price=199, change_pct=None) is False


def test_alert_pct_today_absolute() -> None:
    assert alert_triggered(AlertKind.PCT_TODAY, 3, price=10, change_pct=3.1) is True
    assert alert_triggered(AlertKind.PCT_TODAY, 3, price=10, change_pct=-3) is True
    assert alert_triggered(AlertKind.PCT_TODAY, 3, price=10, change_pct=2.9) is False
    assert alert_triggered(AlertKind.PCT_TODAY, 3, price=10, change_pct=None) is False


def test_calendar_window_and_push_day() -> None:
    today = date(2026, 8, 31)
    assert event_in_window(date(2026, 9, 5), today=today, days=14) is True
    assert event_in_window(date(2026, 9, 20), today=today, days=14) is False
    assert event_in_window(date(2026, 8, 30), today=today, days=14) is False
    assert should_calendar_push(today, today=today) is True
    assert should_calendar_push(date(2026, 9, 1), today=today) is True
    assert should_calendar_push(date(2026, 9, 2), today=today) is False


def test_events_from_extra() -> None:
    rows = events_from_extra(
        "NESN.SW",
        "Nestle",
        {"earnings_date": "2026-09-04", "ex_dividend_date": "2026-09-10"},
    )
    assert [r["kind"] for r in rows] == ["earnings", "ex_dividend"]
    assert rows[0]["date"] == "2026-09-04"
