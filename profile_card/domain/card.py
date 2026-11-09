"""Composes the neofetch-style profile card from its content and the current GitHub stats."""

from datetime import date

from profile_card.domain.card_rows import (
    BlankRow,
    ColumnsRow,
    FieldRow,
    Line,
    Role,
    Row,
    RuleRow,
    SpacerRow,
    Span,
)
from profile_card.domain.profile import Entry, ProfileContent
from profile_card.domain.stats import GitHubStats

MIN_WIDTH = 60
STATS_RIGHT_COLUMN_MIN_WIDTH = 22


def compose_card(content: ProfileContent, stats: GitHubStats, today: date) -> tuple[Line, ...]:
    rows: list[Row] = [RuleRow(content.title), *_about_rows(content, today), BlankRow()]
    if content.contact:
        rows += [RuleRow("- Contact"), *(_entry_row(entry, today) for entry in content.contact), BlankRow()]
    rows += [RuleRow("- GitHub Stats"), *_stats_rows(stats)]
    width = max(MIN_WIDTH, *(row.min_width() for row in rows))
    return tuple(row.render(width) for row in rows)


def _about_rows(content: ProfileContent, today: date) -> list[Row]:
    rows: list[Row] = []
    for group in content.about:
        if rows:
            rows.append(SpacerRow())
        rows.extend(_entry_row(entry, today) for entry in group)
    return rows


def _entry_row(entry: Entry, today: date) -> FieldRow:
    return FieldRow(entry.key, (Span(entry.value_on(today), Role.VALUE),))


def _stats_rows(stats: GitHubStats) -> list[Row]:
    stars = FieldRow("Stars", _number(stats.stars), bulleted=False)
    followers = FieldRow("Followers", _number(stats.followers), bulleted=False)
    right_width = max(STATS_RIGHT_COLUMN_MIN_WIDTH, stars.min_width(), followers.min_width())
    repos = FieldRow(
        "Repos",
        (
            *_number(stats.repositories),
            Span(" {"),
            Span("Contributed", Role.KEY),
            Span(": "),
            *_number(stats.contributed_repositories),
            Span("}"),
        ),
    )
    commits = FieldRow("Commits", _number(stats.commits))
    lines_of_code = FieldRow(
        "Lines of Code on GitHub",
        (
            *_number(stats.net_lines),
            Span(" ( "),
            Span(f"{stats.lines_added:,}", Role.ADDED),
            Span("++", Role.ADDED),
            Span(", "),
            Span(f"{stats.lines_deleted:,}", Role.DELETED),
            Span("--", Role.DELETED),
            Span(" )"),
        ),
    )
    return [ColumnsRow(repos, stars, right_width), ColumnsRow(commits, followers, right_width), lines_of_code]


def _number(amount: int) -> Line:
    return (Span(f"{amount:,}", Role.VALUE),)
