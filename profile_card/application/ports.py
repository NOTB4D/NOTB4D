"""Boundaries the use cases depend on; adapters implement them."""

from collections.abc import Iterable, Mapping
from dataclasses import dataclass
from datetime import date
from typing import Protocol

from profile_card.domain.card_rows import Line
from profile_card.domain.github import Contribution, GitHubUser, Repository
from profile_card.domain.stats import GitHubStats


@dataclass(frozen=True)
class CachedContribution:
    """A contribution counted when the repository had `commit_count` commits."""

    commit_count: int
    contribution: Contribution


class UserDirectory(Protocol):
    def find(self, login: str) -> GitHubUser: ...


class RepositoryCatalog(Protocol):
    def repositories_of(self, login: str) -> list[Repository]:
        """Repositories the user owns, collaborates on, or can see as an organization member."""
        ...


class CommitHistory(Protocol):
    def contribution_to(self, repository: Repository, author_id: str) -> Contribution: ...


class ContributionCache(Protocol):
    def load(self, repository_names: Iterable[str]) -> dict[str, CachedContribution]:
        """Cached entries for the given repositories; unknown names are left out."""
        ...

    def save(self, entries: Mapping[str, CachedContribution]) -> None:
        """Replaces the whole cache with `entries`."""
        ...


class StatsCollector(Protocol):
    def collect(self, login: str) -> GitHubStats: ...


class Clock(Protocol):
    def today(self) -> date: ...


class CardPublisher(Protocol):
    def publish(self, card: tuple[Line, ...]) -> None: ...
