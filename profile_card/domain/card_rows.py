"""Monospace rows of the profile card, styled by role and justified to a shared width."""

from dataclasses import dataclass
from enum import Enum
from typing import Protocol


class Role(Enum):
    TEXT = "text"
    KEY = "key"
    VALUE = "value"
    LEADER = "leader"
    ADDED = "added"
    DELETED = "deleted"


@dataclass(frozen=True)
class Span:
    text: str
    role: Role = Role.TEXT


Line = tuple[Span, ...]


def plain_text(line: Line) -> str:
    return "".join(span.text for span in line)


class Row(Protocol):
    def min_width(self) -> int: ...

    def render(self, width: int) -> Line: ...


_BULLET = ". "
_MIN_LEADER = len(" . ")
_RULE_HEAD = " -"
_RULE_TAIL = "-—-"
_COLUMN_SEPARATOR = " | "


@dataclass(frozen=True)
class FieldRow:
    key: str
    value: Line
    bulleted: bool = True

    def min_width(self) -> int:
        return self._fixed_width() + _MIN_LEADER

    def render(self, width: int) -> Line:
        if width < self.min_width():
            raise ValueError(f"{self.key!r} needs at least {self.min_width()} columns, got {width}")
        dots = width - self._fixed_width() - 2
        return (*self._head(), Span(" " + "." * dots + " ", Role.LEADER), *self.value)

    def _head(self) -> Line:
        bullet = (Span(_BULLET, Role.LEADER),) if self.bulleted else ()
        key_parts: list[Span] = []
        for part in self.key.split("."):
            if key_parts:
                key_parts.append(Span("."))
            key_parts.append(Span(part, Role.KEY))
        return (*bullet, *key_parts, Span(":"))

    def _fixed_width(self) -> int:
        return len(plain_text(self._head())) + len(plain_text(self.value))


@dataclass(frozen=True)
class RuleRow:
    title: str

    def min_width(self) -> int:
        return len(self.title) + len(_RULE_HEAD) + 1 + len(_RULE_TAIL)

    def render(self, width: int) -> Line:
        if width < self.min_width():
            raise ValueError(f"{self.title!r} needs at least {self.min_width()} columns, got {width}")
        fill = width - len(self.title) - len(_RULE_HEAD) - len(_RULE_TAIL)
        return (Span(self.title), Span(_RULE_HEAD + "—" * fill + _RULE_TAIL))


@dataclass(frozen=True)
class SpacerRow:
    def min_width(self) -> int:
        return len(_BULLET)

    def render(self, width: int) -> Line:
        return (Span(_BULLET, Role.LEADER),)


@dataclass(frozen=True)
class BlankRow:
    def min_width(self) -> int:
        return 0

    def render(self, width: int) -> Line:
        return ()


@dataclass(frozen=True)
class ColumnsRow:
    left: FieldRow
    right: FieldRow
    right_width: int

    def __post_init__(self) -> None:
        if self.right_width < self.right.min_width():
            raise ValueError(
                f"right column needs at least {self.right.min_width()} columns, got {self.right_width}"
            )

    def min_width(self) -> int:
        return self.left.min_width() + len(_COLUMN_SEPARATOR) + self.right_width

    def render(self, width: int) -> Line:
        left_width = width - len(_COLUMN_SEPARATOR) - self.right_width
        return (
            *self.left.render(left_width),
            Span(_COLUMN_SEPARATOR),
            *self.right.render(self.right_width),
        )
