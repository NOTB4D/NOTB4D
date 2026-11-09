"""Renders the card as an SVG image: ASCII art on the left, the neofetch-style text on the right."""

import math
from collections.abc import Sequence
from dataclasses import dataclass
from pathlib import Path
from xml.sax.saxutils import escape

from profile_card.domain.card_rows import Line, Role, Span, plain_text

FONT_FAMILY = "ui-monospace, SFMono-Regular, 'SF Mono', Menlo, Consolas, 'Liberation Mono', monospace"
FONT_SIZE = 16
CHAR_WIDTH = 9.65  # widest common monospace advance at 16px (Menlo, DejaVu Sans Mono ≈ 0.602em)
LINE_HEIGHT = 20
PADDING = 15  # above and below the text blocks
FIRST_BASELINE = 30  # PADDING + three quarters of a line
MARGIN = 15
GAP = 25


@dataclass(frozen=True)
class Palette:
    background: str
    text: str
    key: str
    value: str
    added: str
    deleted: str
    leader: str


DARK = Palette(
    background="#161b22",
    text="#c9d1d9",
    key="#ffa657",
    value="#a5d6ff",
    added="#3fb950",
    deleted="#f85149",
    leader="#616e7f",
)

LIGHT = Palette(
    background="#f6f8fa",
    text="#24292f",
    key="#953800",
    value="#0a3069",
    added="#1a7f37",
    deleted="#cf222e",
    leader="#c2cfde",
)


def render_svg(
    card: Sequence[Line], art: Sequence[str], palette: Palette, art_font_size: float = FONT_SIZE
) -> str:
    art_lines = [line.rstrip() for line in art]
    art_scale = art_font_size / FONT_SIZE
    art_columns = max((len(line) for line in art_lines), default=0)
    card_x = math.ceil(MARGIN + art_columns * CHAR_WIDTH * art_scale + GAP) if art_columns else MARGIN
    card_columns = max((len(plain_text(line)) for line in card), default=0)
    width = math.ceil(card_x + card_columns * CHAR_WIDTH + MARGIN)
    height = math.ceil(2 * PADDING + max(len(card) * LINE_HEIGHT, len(art_lines) * LINE_HEIGHT * art_scale))

    parts = [
        "<?xml version='1.0' encoding='UTF-8'?>",
        f'<svg xmlns="http://www.w3.org/2000/svg" width="{width}" height="{height}" '
        f'viewBox="0 0 {width} {height}" font-family="{FONT_FAMILY}" font-size="{FONT_SIZE}px" '
        'xml:space="preserve">',
        _style(palette),
        f'<rect width="{width}" height="{height}" fill="{palette.background}" rx="15"/>',
    ]
    parts += [
        f'<text x="{MARGIN}" y="{_baseline(row, LINE_HEIGHT * art_scale)}" font-size="{art_font_size:g}px" '
        f'fill="{palette.text}">{escape(line)}</text>'
        for row, line in enumerate(art_lines)
        if line
    ]
    parts += [
        f'<text x="{card_x}" y="{_baseline(row, LINE_HEIGHT)}" fill="{palette.text}">'
        f'{"".join(map(_tspan, line))}</text>'
        for row, line in enumerate(card)
        if line
    ]
    parts.append("</svg>")
    return "\n".join(parts) + "\n"


@dataclass(frozen=True)
class SvgTarget:
    path: Path
    palette: Palette
    art: Sequence[str]
    art_font_size: float = FONT_SIZE


class SvgCardFiles:
    """Publishes the card as one SVG file per theme."""

    def __init__(self, targets: Sequence[SvgTarget]):
        self._targets = targets

    def publish(self, card: Sequence[Line]) -> None:
        for target in self._targets:
            svg = render_svg(card, target.art, target.palette, target.art_font_size)
            target.path.write_text(svg, encoding="utf-8")


def _style(palette: Palette) -> str:
    return "\n".join(
        [
            "<style>",
            f".key {{fill: {palette.key};}}",
            f".value {{fill: {palette.value};}}",
            f".added {{fill: {palette.added};}}",
            f".deleted {{fill: {palette.deleted};}}",
            f".leader {{fill: {palette.leader};}}",
            "text, tspan {white-space: pre;}",
            "</style>",
        ]
    )


def _baseline(row: int, line_height: float) -> str:
    offset = (FIRST_BASELINE - PADDING) / LINE_HEIGHT
    return f"{PADDING + (row + offset) * line_height:g}"


def _tspan(span: Span) -> str:
    css_class = "" if span.role is Role.TEXT else f' class="{span.role.value}"'
    return f"<tspan{css_class}>{escape(span.text)}</tspan>"
