"""Hand-written content of the profile card (who the owner is and how to reach them)."""

from dataclasses import dataclass
from datetime import date

from profile_card.domain.elapsed import elapsed_between


@dataclass(frozen=True)
class StaticEntry:
    key: str
    value: str

    def value_on(self, today: date) -> str:
        return self.value


@dataclass(frozen=True)
class UptimeEntry:
    key: str
    since: date

    def value_on(self, today: date) -> str:
        return str(elapsed_between(self.since, today))


Entry = StaticEntry | UptimeEntry


@dataclass(frozen=True)
class ProfileContent:
    title: str
    about: tuple[tuple[Entry, ...], ...]
    contact: tuple[Entry, ...] = ()
