"""Collects the card's GitHub numbers, recounting lines of code only for repositories that changed."""

from profile_card.application.ports import (
    CachedContribution,
    CommitHistory,
    ContributionCache,
    RepositoryCatalog,
    UserDirectory,
)
from profile_card.domain.github import Contribution, Repository
from profile_card.domain.stats import GitHubStats


class CollectGitHubStats:
    def __init__(
        self,
        users: UserDirectory,
        catalog: RepositoryCatalog,
        history: CommitHistory,
        cache: ContributionCache,
    ):
        self._users = users
        self._catalog = catalog
        self._history = history
        self._cache = cache

    def collect(self, login: str) -> GitHubStats:
        user = self._users.find(login)
        repositories = self._catalog.repositories_of(login)
        contributions = self._contributions(repositories, user.id)
        owned = [repository for repository in repositories if repository.is_owned_by(login)]
        return GitHubStats(
            repositories=len(owned),
            contributed_repositories=len(repositories),
            stars=sum(repository.stars for repository in owned),
            commits=sum(contribution.commits for contribution in contributions),
            followers=user.followers,
            lines_added=sum(contribution.additions for contribution in contributions),
            lines_deleted=sum(contribution.deletions for contribution in contributions),
        )

    def _contributions(self, repositories: list[Repository], author_id: str) -> list[Contribution]:
        ledger = self._cache.load([repository.name_with_owner for repository in repositories])
        try:
            for repository in repositories:
                cached = ledger.get(repository.name_with_owner)
                if cached is None or cached.commit_count != repository.commit_count:
                    ledger[repository.name_with_owner] = CachedContribution(
                        repository.commit_count, self._count(repository, author_id)
                    )
        finally:
            self._cache.save(ledger)
        return [ledger[repository.name_with_owner].contribution for repository in repositories]

    def _count(self, repository: Repository, author_id: str) -> Contribution:
        if repository.commit_count == 0:
            return Contribution.none()
        return self._history.contribution_to(repository, author_id)
