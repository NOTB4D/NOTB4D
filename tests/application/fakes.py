"""In-memory test doubles for the application ports."""

from profile_card.application.ports import CachedContribution
from profile_card.domain.github import Contribution, GitHubUser, Repository


class FakeUserDirectory:
    def __init__(self, user: GitHubUser):
        self._user = user
        self.requested_logins: list[str] = []

    def find(self, login: str) -> GitHubUser:
        self.requested_logins.append(login)
        return self._user


class FakeRepositoryCatalog:
    def __init__(self, repositories: list[Repository]):
        self._repositories = repositories

    def repositories_of(self, login: str) -> list[Repository]:
        return list(self._repositories)


class FakeCommitHistory:
    def __init__(self, contributions: dict[str, Contribution], failing: set[str] = frozenset()):
        self._contributions = contributions
        self._failing = failing
        self.requests: list[tuple[str, str]] = []

    def contribution_to(self, repository: Repository, author_id: str) -> Contribution:
        self.requests.append((repository.name_with_owner, author_id))
        if repository.name_with_owner in self._failing:
            raise RuntimeError(f"history of {repository.name_with_owner} is unavailable")
        return self._contributions[repository.name_with_owner]


class FakeContributionCache:
    def __init__(self, entries: dict[str, CachedContribution] | None = None):
        self.entries = dict(entries or {})
        self.saved: dict[str, CachedContribution] | None = None

    def load(self, repository_names) -> dict[str, CachedContribution]:
        return {name: self.entries[name] for name in repository_names if name in self.entries}

    def save(self, entries) -> None:
        self.saved = dict(entries)
        self.entries = dict(entries)
