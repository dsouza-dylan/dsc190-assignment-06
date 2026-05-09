import re
from datetime import date, timedelta
from typing import Optional
from dateutil.parser import parse as dtparse
from dateutil.relativedelta import relativedelta

WEEKDAYS = {
    "monday": 0,
    "tuesday": 1,
    "wednesday": 2,
    "thursday": 3,
    "friday": 4,
    "saturday": 5,
    "sunday": 6,
}


WORD_NUMS = {
    "one": 1,
    "two": 2,
    "three": 3,
    "four": 4,
    "five": 5,
    "six": 6,
    "seven": 7,
    "eight": 8,
    "nine": 9,
    "ten": 10,
}


def apply_offset(base: date, amount: int, unit: str) -> date:
    if unit.startswith("day"):
        return base + timedelta(days=amount)

    if unit.startswith("week"):
        return base + timedelta(weeks=amount)

    if unit.startswith("month"):
        return base + relativedelta(months=amount)

    if unit.startswith("year"):
        return base + relativedelta(years=amount)

    raise ValueError(f"Unknown unit: {unit}")


def next_weekday(base: date, target: int) -> date:
    days_ahead = (target - base.weekday()) % 7

    if days_ahead == 0:
        days_ahead = 7

    return base + timedelta(days=days_ahead)


def last_weekday(base: date, target: int) -> date:
    days_behind = (base.weekday() - target) % 7

    if days_behind == 0:
        days_behind = 7

    return base - timedelta(days=days_behind)


def parse_amount(value: str) -> int:
    if value in {"a", "an"}:
        return 1

    if value in WORD_NUMS:
        return WORD_NUMS[value]

    return int(value)


def parse(s: str, today: Optional[date] = None) -> date:
    if today is None:
        today = date.today()

    s = s.lower().strip()

    s = re.sub(r"(\d+)(st|nd|rd|th)", r"\1", s)

    if s == "today":
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    match = re.fullmatch(
        r"in (\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (days?|weeks?|months?|years?)",
        s,
    )

    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)

        return apply_offset(today, amount, unit)

    match = re.fullmatch(
        r"(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (days?|weeks?|months?|years?) ago",
        s,
    )

    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)

        return apply_offset(today, -amount, unit)

    match = re.fullmatch(
        r"(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (days?|weeks?|months?|years?) before (.+)",
        s,
    )

    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)
        target = parse(match.group(3), today)

        return apply_offset(target, -amount, unit)

    match = re.fullmatch(
        r"(\d+|a|an|one|two|three|four|five|six|seven|eight|nine|ten) (days?|weeks?|months?|years?) after (.+)",
        s,
    )

    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)
        target = parse(match.group(3), today)

        return apply_offset(target, amount, unit)

    match = re.fullmatch(r"next (\w+)", s)

    if match:
        weekday = match.group(1)

        if weekday in WEEKDAYS:
            return next_weekday(today, WEEKDAYS[weekday])

    match = re.fullmatch(r"last (\w+)", s)

    if match:
        weekday = match.group(1)

        if weekday in WEEKDAYS:
            return last_weekday(today, WEEKDAYS[weekday])

    try:
        return dtparse(s).date()
    except Exception as exc:
        raise ValueError(f"Could not parse: {s}") from exc
