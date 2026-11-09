"""Wall-clock implementation of the Clock port."""

from collections.abc import Callable
from datetime import date, datetime, timezone


def _utc_now() -> datetime:
    return datetime.now(timezone.utc)


class SystemClock:
    def __init__(self, now: Callable[[], datetime] = _utc_now):
        self._now = now

    def today(self) -> date:
        return self._now().date()
