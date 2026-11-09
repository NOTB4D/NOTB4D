"""Reads the card's hand-written content from profile.json."""

import json
from datetime import date
from pathlib import Path
from typing import Any

from profile_card.domain.profile import Entry, ProfileContent, StaticEntry, UptimeEntry


def load_profile_content(path: Path) -> ProfileContent:
    document = json.loads(path.read_text(encoding="utf-8"))
    return ProfileContent(
        title=document["title"],
        about=tuple(tuple(_entry(raw) for raw in group) for group in document["about"]),
        contact=tuple(_entry(raw) for raw in document.get("contact", [])),
    )


def _entry(raw: dict[str, Any]) -> Entry:
    key = raw["key"]
    if ("value" in raw) == ("since" in raw):
        raise ValueError(f"Entry {key!r} needs exactly one of 'value' or 'since'")
    if "value" in raw:
        return StaticEntry(key, raw["value"])
    try:
        return UptimeEntry(key, date.fromisoformat(raw["since"]))
    except ValueError as error:
        raise ValueError(f"Entry {key!r} has an invalid 'since' date: {raw['since']!r}") from error
