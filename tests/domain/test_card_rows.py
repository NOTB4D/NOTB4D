import unittest

from profile_card.domain.card_rows import (
    BlankRow,
    ColumnsRow,
    FieldRow,
    Role,
    RuleRow,
    Span,
    SpacerRow,
    plain_text,
)


def value(text):
    return (Span(text, Role.VALUE),)


class FieldRowTests(unittest.TestCase):
    def test_fills_the_gap_between_key_and_value_with_a_dot_leader(self):
        line = FieldRow("OS", value("macOS, iOS")).render(30)

        self.assertEqual(plain_text(line), ". OS: " + "." * 13 + " macOS, iOS")
        self.assertEqual(len(plain_text(line)), 30)

    def test_styles_bullet_key_leader_and_value(self):
        line = FieldRow("OS", value("macOS")).render(20)

        self.assertEqual(
            [(span.text, span.role) for span in line],
            [
                (". ", Role.LEADER),
                ("OS", Role.KEY),
                (":", Role.TEXT),
                (" " + "." * 8 + " ", Role.LEADER),
                ("macOS", Role.VALUE),
            ],
        )

    def test_splits_a_dotted_key_into_key_parts_joined_by_a_plain_dot(self):
        line = FieldRow("Languages.Real", value("Turkish")).render(40)

        self.assertEqual(
            [(span.text, span.role) for span in line[1:4]],
            [("Languages", Role.KEY), (".", Role.TEXT), ("Real", Role.KEY)],
        )

    def test_minimum_width_leaves_room_for_a_single_dot(self):
        row = FieldRow("OS", value("macOS"))

        self.assertEqual(row.min_width(), len(". OS:") + len(" . ") + len("macOS"))
        self.assertEqual(plain_text(row.render(row.min_width())), ". OS: . macOS")

    def test_can_omit_the_bullet(self):
        line = FieldRow("Stars", value("7"), bulleted=False).render(14)

        self.assertEqual(plain_text(line), "Stars: ..... 7")


class RuleRowTests(unittest.TestCase):
    def test_extends_the_title_with_a_rule_to_the_full_width(self):
        line = RuleRow("eser@kucuker").render(25)

        self.assertEqual(plain_text(line), "eser@kucuker -" + "—" * 8 + "-—-")
        self.assertEqual(len(plain_text(line)), 25)

    def test_minimum_width_keeps_one_rule_segment(self):
        row = RuleRow("- Contact")

        self.assertEqual(plain_text(row.render(row.min_width())), "- Contact -—-—-")


class SeparatorRowTests(unittest.TestCase):
    def test_spacer_row_is_a_lone_bullet(self):
        self.assertEqual(SpacerRow().render(60), (Span(". ", Role.LEADER),))

    def test_blank_row_is_empty(self):
        self.assertEqual(BlankRow().render(60), ())
        self.assertEqual(BlankRow().min_width(), 0)


class ColumnsRowTests(unittest.TestCase):
    def test_renders_two_fields_separated_by_a_bar_with_a_fixed_right_column(self):
        row = ColumnsRow(
            FieldRow("Commits", value("1,234")),
            FieldRow("Followers", value("17"), bulleted=False),
            right_width=18,
        )

        text = plain_text(row.render(40))

        self.assertEqual(text, ". Commits: .. 1,234 | Followers: .... 17")
        self.assertEqual(text.index(" | "), 40 - 18 - 3)

    def test_minimum_width_is_left_minimum_plus_separator_plus_right_column(self):
        row = ColumnsRow(
            FieldRow("Commits", value("1,234")),
            FieldRow("Followers", value("17"), bulleted=False),
            right_width=18,
        )

        self.assertEqual(row.min_width(), FieldRow("Commits", value("1,234")).min_width() + 3 + 18)

    def test_rejects_a_right_column_narrower_than_its_field(self):
        with self.assertRaises(ValueError):
            ColumnsRow(
                FieldRow("Commits", value("1")),
                FieldRow("Followers", value("17"), bulleted=False),
                right_width=5,
            )


if __name__ == "__main__":
    unittest.main()
