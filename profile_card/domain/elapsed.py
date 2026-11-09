"""Calendar time elapsed between two dates, e.g. the card's "Uptime"."""

import calendar
from dataclasses import dataclass
from datetime import date


@dataclass(frozen=True)
class Elapsed:
    years: int
    months: int
    days: int

    def __str__(self) -> str:
        return ", ".join(
            _quantity(amount, unit)
            for amount, unit in ((self.years, "year"), (self.months, "month"), (self.days, "day"))
        )


def elapsed_between(start: date, end: date) -> Elapsed:
    if end < start:
        raise ValueError(f"end ({end}) is before start ({start})")
    months = (end.year - start.year) * 12 + (end.month - start.month)
    if _add_months(start, months) > end:
        months -= 1
    days = (end - _add_months(start, months)).days
    return Elapsed(years=months // 12, months=months % 12, days=days)


def _add_months(day: date, months: int) -> date:
    month_index = day.month - 1 + months
    year, month = day.year + month_index // 12, month_index % 12 + 1
    return date(year, month, min(day.day, calendar.monthrange(year, month)[1]))


def _quantity(amount: int, unit: str) -> str:
    return f"{amount} {unit}{'' if amount == 1 else 's'}"
