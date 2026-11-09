"""Composition root: wires adapters and drivers to the use cases, then refreshes the card."""

import os
from collections.abc import Mapping
from pathlib import Path

from profile_card.adapters.contribution_cache_file import FileContributionCache
from profile_card.adapters.github_graphql import (
    GraphQLCommitHistory,
    GraphQLRepositoryCatalog,
    GraphQLTransport,
    GraphQLUserDirectory,
)
from profile_card.adapters.profile_json import load_profile_content
from profile_card.adapters.svg_card import DARK, LIGHT, SvgCardFiles, SvgTarget
from profile_card.application.collect_stats import CollectGitHubStats
from profile_card.application.ports import Clock
from profile_card.application.refresh_card import RefreshProfileCard
from profile_card.drivers.http_graphql import UrllibGraphQLTransport
from profile_card.drivers.system_clock import SystemClock

REPOSITORY_ROOT = Path(__file__).resolve().parent.parent
PORTRAIT_FONT_SIZE = 12  # assets/ascii-*.txt are drawn for 12px glyphs (28 rows beside the card)


def build_refresh(root: Path, transport: GraphQLTransport, clock: Clock) -> RefreshProfileCard:
    stats = CollectGitHubStats(
        users=GraphQLUserDirectory(transport),
        catalog=GraphQLRepositoryCatalog(transport),
        history=GraphQLCommitHistory(transport),
        cache=FileContributionCache(root / "cache" / "contributions.txt"),
    )
    publisher = SvgCardFiles(
        [
            SvgTarget(root / "dark_mode.svg", DARK, _art(root / "assets" / "ascii-dark.txt"), PORTRAIT_FONT_SIZE),
            SvgTarget(root / "light_mode.svg", LIGHT, _art(root / "assets" / "ascii-light.txt"), PORTRAIT_FONT_SIZE),
        ]
    )
    return RefreshProfileCard(
        stats=stats,
        content=load_profile_content(root / "profile.json"),
        clock=clock,
        publisher=publisher,
    )


def main(environ: Mapping[str, str] = os.environ) -> None:
    transport = UrllibGraphQLTransport(environ["ACCESS_TOKEN"])
    build_refresh(REPOSITORY_ROOT, transport, SystemClock()).execute(environ["USER_NAME"])


def _art(path: Path) -> list[str]:
    return path.read_text(encoding="utf-8").splitlines()
