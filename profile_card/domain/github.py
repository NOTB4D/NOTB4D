"""GitHub concepts the card's numbers are derived from."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubUser:
    id: str
    followers: int


@dataclass(frozen=True)
class Repository:
    name_with_owner: str
    stars: int
    commit_count: int

    @property
    def owner(self) -> str:
        return self.name_with_owner.split("/", 1)[0]

    def is_owned_by(self, login: str) -> bool:
        return self.owner.casefold() == login.casefold()


@dataclass(frozen=True)
class Contribution:
    """The user's own commits on a repository's default branch and the lines they changed."""

    commits: int
    additions: int
    deletions: int

    @classmethod
    def none(cls) -> "Contribution":
        return cls(commits=0, additions=0, deletions=0)
