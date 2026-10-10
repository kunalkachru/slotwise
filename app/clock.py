"""The only source of "now". Tests patch `app.clock.now` to freeze time."""

from datetime import datetime
from zoneinfo import ZoneInfo

BERLIN = ZoneInfo("Europe/Berlin")


def now() -> datetime:
    return datetime.now(BERLIN)
