import math
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from profile_card.adapters.svg_card import (
    CHAR_WIDTH,
    FIRST_BASELINE,
    GAP,
    LINE_HEIGHT,
    MARGIN,
    Palette,
    SvgCardFiles,
    SvgTarget,
    render_svg,
)
from profile_card.domain.card_rows import Role, Span

SVG = "{http://www.w3.org/2000/svg}"

CARD = (
    (Span("eser@kucuker"), Span(" -—-")),
    (Span(". ", Role.LEADER), Span("OS", Role.KEY), Span(":"), Span(" .. ", Role.LEADER), Span("macOS", Role.VALUE)),
    (),
    (Span("150", Role.ADDED), Span("--", Role.DELETED)),
)
ART = ("  @@   ", " @&<@ ", "")
PALETTE = Palette(
    background="#000001",
    text="#000002",
    key="#000003",
    value="#000004",
    added="#000005",
    deleted="#000006",
    leader="#000007",
)


def parse(svg):
    return ET.fromstring(svg)


def texts_at(root, x):
    return [element for element in root.iter(f"{SVG}text") if element.get("x") == str(x)]


CARD_X = math.ceil(MARGIN + 5 * CHAR_WIDTH + GAP)


class RenderSvgTests(unittest.TestCase):
    def setUp(self):
        self.root = parse(render_svg(CARD, ART, PALETTE))

    def test_renders_an_svg_document(self):
        self.assertEqual(self.root.tag, f"{SVG}svg")

    def test_draws_each_art_line_on_its_own_row_at_the_left_margin(self):
        art = texts_at(self.root, MARGIN)

        self.assertEqual([element.text for element in art], ["  @@", " @&<@"])
        self.assertEqual([element.get("y") for element in art], [str(FIRST_BASELINE), str(FIRST_BASELINE + LINE_HEIGHT)])

    def test_starts_the_card_after_the_widest_art_line_and_a_gap(self):
        card = texts_at(self.root, CARD_X)

        self.assertEqual(len(card), 3)
        self.assertEqual("".join(card[0].itertext()), "eser@kucuker -—-")

    def test_styles_card_spans_by_role(self):
        os_line = texts_at(self.root, CARD_X)[1]

        self.assertEqual(
            [(tspan.get("class"), tspan.text) for tspan in os_line],
            [("leader", ". "), ("key", "OS"), (None, ":"), ("leader", " .. "), ("value", "macOS")],
        )

    def test_keeps_the_row_of_a_blank_card_line(self):
        last = texts_at(self.root, CARD_X)[2]

        self.assertEqual(last.get("y"), str(FIRST_BASELINE + 3 * LINE_HEIGHT))
        self.assertEqual([(t.get("class"), t.text) for t in last], [("added", "150"), ("deleted", "--")])

    def test_sizes_the_canvas_to_fit_the_art_and_the_card(self):
        width = math.ceil(CARD_X + len("eser@kucuker -—-") * CHAR_WIDTH + MARGIN)
        height = FIRST_BASELINE + 3 * LINE_HEIGHT + 20

        self.assertEqual((self.root.get("width"), self.root.get("height")), (str(width), str(height)))
        self.assertEqual(self.root.get("viewBox"), f"0 0 {width} {height}")

    def test_paints_with_the_palette(self):
        style = self.root.find(f"{SVG}style").text
        background = self.root.find(f"{SVG}rect")

        for css in (
            ".key {fill: #000003;}",
            ".value {fill: #000004;}",
            ".added {fill: #000005;}",
            ".deleted {fill: #000006;}",
            ".leader {fill: #000007;}",
        ):
            self.assertIn(css, style)
        self.assertEqual(background.get("fill"), "#000001")
        self.assertEqual({element.get("fill") for element in self.root.iter(f"{SVG}text")}, {"#000002"})

    def test_preserves_runs_of_spaces(self):
        self.assertIn("white-space: pre;", self.root.find(f"{SVG}style").text)
        self.assertEqual(self.root.get("{http://www.w3.org/XML/1998/namespace}space"), "preserve")

    def test_places_the_card_at_the_margin_without_art(self):
        root = parse(render_svg(CARD, (), PALETTE))

        self.assertEqual(len(texts_at(root, MARGIN)), 3)


class SmallerArtTests(unittest.TestCase):
    def setUp(self):
        self.root = parse(render_svg(CARD, ART, PALETTE, art_font_size=12))

    def test_draws_the_art_with_its_own_font_size_and_line_height(self):
        art = texts_at(self.root, MARGIN)

        self.assertEqual({element.get("font-size") for element in art}, {"12px"})
        self.assertEqual([element.get("y") for element in art], ["26.25", "41.25"])

    def test_measures_the_art_width_at_its_font_size(self):
        card_x = math.ceil(MARGIN + 5 * CHAR_WIDTH * 12 / 16 + GAP)

        self.assertEqual(len(texts_at(self.root, card_x)), 3)

    def test_keeps_the_card_at_its_own_size(self):
        card = [element for element in self.root.iter(f"{SVG}text") if element.get("x") != str(MARGIN)]

        self.assertEqual({element.get("font-size") for element in card}, {None})
        self.assertEqual(card[0].get("y"), str(FIRST_BASELINE))

    def test_grows_the_canvas_to_fit_a_taller_art(self):
        tall_art = ["@"] * 10

        root = parse(render_svg(CARD, tall_art, PALETTE, art_font_size=12))

        self.assertEqual(root.get("height"), str(15 + 10 * 15 + 15))


class SvgCardFilesTests(unittest.TestCase):
    def test_writes_one_svg_per_target(self):
        with tempfile.TemporaryDirectory() as directory:
            dark, light = Path(directory, "dark_mode.svg"), Path(directory, "light_mode.svg")
            other = Palette(*(f"#1{index:05d}" for index in range(7)))
            publisher = SvgCardFiles(
                [SvgTarget(dark, PALETTE, ART, art_font_size=12), SvgTarget(light, other, ("x",))]
            )

            publisher.publish(CARD)

            self.assertEqual(dark.read_text(encoding="utf-8"), render_svg(CARD, ART, PALETTE, art_font_size=12))
            self.assertEqual(light.read_text(encoding="utf-8"), render_svg(CARD, ("x",), other))


if __name__ == "__main__":
    unittest.main()
