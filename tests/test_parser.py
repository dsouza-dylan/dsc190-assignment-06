from datetime import date

from nldate import parse

TODAY = date(2025, 5, 1)


def test_today():
    assert parse("today", TODAY) == TODAY


def test_tomorrow():
    assert parse("tomorrow", TODAY) == date(2025, 5, 2)


def test_yesterday():
    assert parse("yesterday", TODAY) == date(2025, 4, 30)


def test_in_days():
    assert parse("in 5 days", TODAY) == date(2025, 5, 6)


def test_days_ago():
    assert parse("3 days ago", TODAY) == date(2025, 4, 28)


def test_weeks():
    assert parse("in 2 weeks", TODAY) == date(2025, 5, 15)


def test_months():
    assert parse("in 1 month", TODAY) == date(2025, 6, 1)


def test_absolute_date():
    assert parse("December 1st, 2025") == date(2025, 12, 1)


def test_before():
    assert parse("5 days before December 1st, 2025") == date(2025, 11, 26)


def test_after():
    assert parse("2 weeks after January 1st, 2025") == date(2025, 1, 15)


def test_next_tuesday():
    assert parse(
        "next tuesday",
        TODAY,
    ) == date(2025, 5, 6)


def test_last_friday():
    assert parse(
        "last friday",
        TODAY,
    ) == date(2025, 4, 25)
