import re
import unittest
from datetime import date

from profile_card.domain.card import compose_card
from profile_card.domain.card_rows import Role, plain_text
from profile_card.domain.profile import ProfileContent, StaticEntry, UptimeEntry
from profile_card.domain.stats import GitHubStats

TODAY = date(2026, 11, 9)

STATS = GitHubStats(
    repositories=26,
    contributed_repositories=30,
    stars=7,
    commits=1234,
    followers=17,
    lines_added=150_000,
    lines_deleted=26_544,
)

CONTENT = ProfileContent(
    title="eser@kucuker",
    about=(
        (
            StaticEntry("OS", "macOS, iOS"),
            UptimeEntry("Uptime", date(2020, 12, 12)),
            StaticEntry("Host", "Mobven"),
            StaticEntry("Kernel", "iOS Developer"),
            StaticEntry("IDE", "Xcode"),
        ),
        (
            StaticEntry("Languages.Programming", "Swift, C#, TypeScript, Python"),
            StaticEntry("Languages.Computer", "JSON, YAML, Markdown"),
            StaticEntry("Languages.Real", "Turkish, English"),
        ),
        (StaticEntry("Hobbies", "Coding, Reading documentation"),),
    ),
    contact=(
        StaticEntry("Email.Work", "eser.kucuker@mobven.com"),
        StaticEntry("GitHub", "NOTB4D"),
    ),
)


def texts(lines):
    return [plain_text(line) for line in lines]


def justified(lines):
    return [text for text in texts(lines) if text not in ("", ". ")]


class ComposeCardLayoutTests(unittest.TestCase):
    def setUp(self):
        self.lines = texts(compose_card(CONTENT, STATS, TODAY))

    def test_starts_with_the_title_rule(self):
        self.assertRegex(self.lines[0], r"^eser@kucuker -—+-—-$")

    def test_lists_about_groups_separated_by_spacer_rows(self):
        keys = [re.match(r"^(\. [^:]*:|\. $|$|- [A-Za-z ]+)", text).group(0) for text in self.lines[1:12]]

        self.assertEqual(
            keys,
            [
                ". OS:", ". Uptime:", ". Host:", ". Kernel:", ". IDE:",
                ". ",
                ". Languages.Programming:", ". Languages.Computer:", ". Languages.Real:",
                ". ",
                ". Hobbies:",
            ],
        )

    def test_shows_the_uptime_for_today(self):
        self.assertRegex(self.lines[2], r"^\. Uptime: \.+ 5 years, 10 months, 28 days$")

    def test_follows_with_the_contact_section(self):
        self.assertEqual(self.lines[12], "")
        self.assertRegex(self.lines[13], r"^- Contact -—+-—-$")
        self.assertRegex(self.lines[14], r"^\. Email\.Work: \.+ eser\.kucuker@mobven\.com$")
        self.assertRegex(self.lines[15], r"^\. GitHub: \.+ NOTB4D$")
        self.assertEqual(self.lines[16], "")

    def test_ends_with_the_github_stats_section(self):
        self.assertRegex(self.lines[17], r"^- GitHub Stats -—+-—-$")
        self.assertRegex(self.lines[18], r"^\. Repos: \.+ 26 \{Contributed: 30\} \| Stars: \.+ 7$")
        self.assertRegex(self.lines[19], r"^\. Commits: \.+ 1,234 \| Followers: \.+ 17$")
        self.assertRegex(
            self.lines[20], r"^\. Lines of Code on GitHub: \.+ 123,456 \( 150,000\+\+, 26,544-- \)$"
        )
        self.assertEqual(len(self.lines), 21)

    def test_justifies_every_content_line_to_sixty_columns(self):
        self.assertEqual({len(text) for text in justified(compose_card(CONTENT, STATS, TODAY))}, {60})

    def test_aligns_the_stats_columns_with_a_twenty_two_column_right_side(self):
        repos, commits = self.lines[18], self.lines[19]

        self.assertEqual(repos.index(" | "), commits.index(" | "))
        self.assertEqual(len(repos) - repos.index(" | ") - len(" | "), 22)


class ComposeCardAdaptationTests(unittest.TestCase):
    def test_widens_every_line_to_fit_a_long_value(self):
        long_value = "x" * 70
        content = ProfileContent(title="eser@kucuker", about=((StaticEntry("OS", long_value),),))

        lines = justified(compose_card(content, STATS, TODAY))

        self.assertEqual(len({len(text) for text in lines}), 1)
        self.assertIn(". OS: . " + long_value, lines)

    def test_omits_the_contact_section_without_contact_entries(self):
        content = ProfileContent(title="eser@kucuker", about=((StaticEntry("OS", "macOS"),),))

        lines = texts(compose_card(content, STATS, TODAY))

        self.assertFalse(any(text.startswith("- Contact") for text in lines))
        self.assertEqual(lines[2], "")
        self.assertRegex(lines[3], r"^- GitHub Stats ")


class ComposeCardStylingTests(unittest.TestCase):
    def test_colors_added_and_deleted_line_counts(self):
        loc_line = compose_card(CONTENT, STATS, TODAY)[20]

        styled = [(span.text, span.role) for span in loc_line if span.role in (Role.ADDED, Role.DELETED)]

        self.assertEqual(
            styled,
            [("150,000", Role.ADDED), ("++", Role.ADDED), ("26,544", Role.DELETED), ("--", Role.DELETED)],
        )

    def test_shows_numbers_as_values(self):
        repos_line = compose_card(CONTENT, STATS, TODAY)[18]

        values = [span.text for span in repos_line if span.role is Role.VALUE]

        self.assertEqual(values, ["26", "30", "7"])


if __name__ == "__main__":
    unittest.main()
