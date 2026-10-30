"""Read the studio's English opening-hours text and say whether it is open at a given moment.

Understood format: parts separated by "·" (or ";", "|", a new line), each part being a day or
day range followed by a time window or "closed":

    Mon 10:00–19:00 · Tue–Fri 9:00–19:00 · Sat 9–17 · Sun closed

Anything else gives `None` ("unknown") rather than a guess.
"""

import re
from datetime import datetime
from zoneinfo import ZoneInfo

from app import clock

DAYS = {"mon": 0, "tue": 1, "wed": 2, "thu": 3, "fri": 4, "sat": 5, "sun": 6}

_DAY = r"(?:mon|tue|wed|thu|fri|sat|sun)[a-z]*"
_TIME = r"\d{1,2}(?::\d{2})?"
_DASH = r"\s*(?:–|—|-|\bto\b)\s*"
_PART = re.compile(
    rf"^(?P<first>{_DAY})(?:{_DASH}(?P<last>{_DAY}))?\s+"
    rf"(?:(?P<closed>closed)|(?P<start>{_TIME}){_DASH}(?P<end>{_TIME}))$",
    re.IGNORECASE,
)
_SPLIT = re.compile(r"[·•;|\n]")

Windows = dict[int, list[tuple[int, int]]]


def _minutes(text: str) -> int | None:
    hours, _, minutes = text.partition(":")
    total = int(hours) * 60 + int(minutes or 0)
    if int(hours) > 24 or int(minutes or 0) > 59 or total > 24 * 60:
        return None
    return total


def parse_opening_hours(text: str | None) -> Windows | None:
    """{weekday (Mon=0): [(start_minute, end_minute), ...]}; a closed day has an empty list.
    `None` when the text is empty or any part is not understood."""
    parts = [" ".join(p.split()) for p in _SPLIT.split(text or "")]
    parts = [p for p in parts if p]
    if not parts:
        return None
    windows: Windows = {day: [] for day in range(7)}
    for part in parts:
        match = _PART.match(part)
        if match is None:
            return None
        first = DAYS[match["first"][:3].lower()]
        last = DAYS[match["last"][:3].lower()] if match["last"] else first
        days = [(first + i) % 7 for i in range((last - first) % 7 + 1)]
        if match["closed"]:
            continue
        start, end = _minutes(match["start"]), _minutes(match["end"])
        if start is None or end is None or start >= end:
            return None
        for day in days:
            windows[day].append((start, end))
    return windows


def is_open_at(text: str | None, moment: datetime, tz: ZoneInfo = clock.BERLIN) -> bool | None:
    """Whether the studio is open at `moment`, judged in the studio time zone.
    The start is inclusive, the end exclusive. `None` if the text can't be read."""
    windows = parse_opening_hours(text)
    if windows is None:
        return None
    local = moment.astimezone(tz)
    minute = local.hour * 60 + local.minute
    return any(start <= minute < end for start, end in windows[local.weekday()])
