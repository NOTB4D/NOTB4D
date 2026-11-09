"""Aggregate GitHub numbers shown on the profile card."""

from dataclasses import dataclass


@dataclass(frozen=True)
class GitHubStats:
    repositories: int
    contributed_repositories: int
    stars: int
    commits: int
    followers: int
    lines_added: int
    lines_deleted: int

    @property
    def net_lines(self) -> int:
        return self.lines_added - self.lines_deleted
