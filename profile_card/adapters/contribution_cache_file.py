"""Contribution cache kept in the repository, so daily runs only recount repositories that changed."""

import hashlib
from collections.abc import Iterable, Mapping
from pathlib import Path

from profile_card.application.ports import CachedContribution
from profile_card.domain.github import Contribution

HEADER = (
    "# Profile card contribution cache. Repository names are SHA-256 hashed to keep private names private.\n"
    "# <repository hash> <commit count> <my commits> <lines added> <lines deleted>\n"
)


class FileContributionCache:
    def __init__(self, path: Path):
        self._path = path

    def load(self, repository_names: Iterable[str]) -> dict[str, CachedContribution]:
        stored = self._read()
        return {name: stored[_digest(name)] for name in repository_names if _digest(name) in stored}

    def save(self, entries: Mapping[str, CachedContribution]) -> None:
        lines = sorted(
            f"{_digest(name)} {entry.commit_count} {entry.contribution.commits} "
            f"{entry.contribution.additions} {entry.contribution.deletions}\n"
            for name, entry in entries.items()
        )
        self._path.parent.mkdir(parents=True, exist_ok=True)
        self._path.write_text(HEADER + "".join(lines), encoding="utf-8")

    def _read(self) -> dict[str, CachedContribution]:
        if not self._path.exists():
            return {}
        stored = {}
        for line in self._path.read_text(encoding="utf-8").splitlines():
            if not line.strip() or line.startswith("#"):
                continue
            digest, commit_count, commits, additions, deletions = line.split()
            stored[digest] = CachedContribution(
                int(commit_count), Contribution(int(commits), int(additions), int(deletions))
            )
        return stored


def _digest(repository_name: str) -> str:
    return hashlib.sha256(repository_name.encode("utf-8")).hexdigest()
