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
    "eleven": 11,
    "twelve": 12,
    "thirteen": 13,
    "fourteen": 14,
    "fifteen": 15,
    "sixteen": 16,
    "seventeen": 17,
    "eighteen": 18,
    "nineteen": 19,
    "twenty": 20,
    "thirty": 30,
    "forty": 40,
    "fifty": 50,
    "sixty": 60,
    "ninety": 90,
    "hundred": 100,
}


_WORD_NUM_PAT = "|".join(sorted(WORD_NUMS.keys(), key=len, reverse=True))
_AMOUNT_PAT = rf"(\d+|a|an|{_WORD_NUM_PAT})"
_UNIT_PAT = r"(days?|weeks?|months?|years?)"


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

    if s in ("today", "now"):
        return today

    if s == "tomorrow":
        return today + timedelta(days=1)

    if s == "yesterday":
        return today - timedelta(days=1)

    if s == "the day after tomorrow":
        return today + timedelta(days=2)

    if s == "the day before yesterday":
        return today - timedelta(days=2)

    # "in X units"
    match = re.fullmatch(rf"in {_AMOUNT_PAT} {_UNIT_PAT}", s)
    if match:
        return apply_offset(today, parse_amount(match.group(1)), match.group(2))

    # "X units ago"
    match = re.fullmatch(rf"{_AMOUNT_PAT} {_UNIT_PAT} ago", s)
    if match:
        return apply_offset(today, -parse_amount(match.group(1)), match.group(2))

    # "X units from now/today/tomorrow/yesterday/<date>"
    match = re.fullmatch(rf"{_AMOUNT_PAT} {_UNIT_PAT} from (.+)", s)
    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)
        anchor_str = match.group(3)
        anchor = parse(anchor_str, today)
        return apply_offset(anchor, amount, unit)

    # "X units before <date>"
    match = re.fullmatch(rf"{_AMOUNT_PAT} {_UNIT_PAT} before (.+)", s)
    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)
        target = parse(match.group(3), today)
        return apply_offset(target, -amount, unit)

    # "X units after <date>"
    match = re.fullmatch(rf"{_AMOUNT_PAT} {_UNIT_PAT} after (.+)", s)
    if match:
        amount = parse_amount(match.group(1))
        unit = match.group(2)
        target = parse(match.group(3), today)
        return apply_offset(target, amount, unit)

    # compound: "X units[, | and ]Y units... before/after/from <date>"
    _offset_part = rf"{_AMOUNT_PAT} {_UNIT_PAT}"
    _offset_list = rf"(?:{_offset_part})(?:(?:,\s*|\s+and\s+)(?:{_offset_part}))*"
    for prep in ("before", "after", "from"):
        pattern = rf"({_offset_list})\s+{prep}\s+(?P<date_str>.+)"
        m = re.fullmatch(pattern, s)
        if m:
            offsets_str = m.group(1)
            date_str = m.group("date_str")
            sign = -1 if prep == "before" else 1
            target = parse(date_str, today)
            for part in re.split(r",\s*|\s+and\s+", offsets_str):
                m2 = re.fullmatch(rf"{_AMOUNT_PAT} {_UNIT_PAT}", part.strip())
                if m2:
                    target = apply_offset(
                        target, sign * parse_amount(m2.group(1)), m2.group(2)
                    )
            return target

    # "next <weekday>" or "next week/month/year"
    match = re.fullmatch(r"next (\w+)", s)
    if match:
        word = match.group(1)
        if word in WEEKDAYS:
            return next_weekday(today, WEEKDAYS[word])
        if word == "week":
            return today + timedelta(weeks=1)
        if word == "month":
            return today + relativedelta(months=1)
        if word == "year":
            return today + relativedelta(years=1)

    # "last <weekday>" or "last week/month/year"
    match = re.fullmatch(r"last (\w+)", s)
    if match:
        word = match.group(1)
        if word in WEEKDAYS:
            return last_weekday(today, WEEKDAYS[word])
        if word == "week":
            return today - timedelta(weeks=1)
        if word == "month":
            return today - relativedelta(months=1)
        if word == "year":
            return today - relativedelta(years=1)

    # "this <weekday>"
    match = re.fullmatch(r"this (\w+)", s)
    if match:
        word = match.group(1)
        if word in WEEKDAYS:
            days_ahead = (WEEKDAYS[word] - today.weekday()) % 7
            return today + timedelta(days=days_ahead)

    try:
        return dtparse(s).date()
    except Exception as exc:
        raise ValueError(f"Could not parse: {s}") from exc
