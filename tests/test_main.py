import json
import tempfile
import unittest
import xml.etree.ElementTree as ET
from pathlib import Path

from profile_card.adapters.github_graphql import HISTORY_QUERY, REPOSITORIES_QUERY, USER_QUERY
from profile_card.main import build_refresh
from tests.domain.test_card import TODAY

PROFILE = {
    "title": "eser@kucuker",
    "about": [[{"key": "OS", "value": "macOS, iOS"}, {"key": "Uptime", "since": "2020-12-12"}]],
    "contact": [{"key": "GitHub", "value": "NOTB4D"}],
}

REPOSITORIES = {
    "NOTB4D/QuizApp": (2, [("U1", 900, 100), ("U2", 50, 5)]),
    "NOTB4D/PhotoApp": (1, [("U1", 1_200, 200)]),
    "Mobven/IAPKit": (40, [("U1", 10_000, 1_000), ("U1", 400, 600)]),
}


class GitHubDouble:
    """Answers the adapter's three queries from REPOSITORIES and counts history requests."""

    def __init__(self):
        self.history_requests = 0

    def execute(self, query, variables):
        if query == USER_QUERY:
            return {"user": {"id": "U1", "followers": {"totalCount": 17}}}
        if query == REPOSITORIES_QUERY:
            nodes = [
                {
                    "nameWithOwner": name,
                    "stargazers": {"totalCount": stars},
                    "defaultBranchRef": {"target": {"history": {"totalCount": len(commits)}}},
                }
                for name, (stars, commits) in REPOSITORIES.items()
            ]
            return {"user": {"repositories": {"nodes": nodes, "pageInfo": {"endCursor": None, "hasNextPage": False}}}}
        if query == HISTORY_QUERY:
            self.history_requests += 1
            _, commits = REPOSITORIES[f"{variables['owner']}/{variables['name']}"]
            nodes = [{"additions": a, "deletions": d, "author": {"user": {"id": author}}} for author, a, d in commits]
            history = {"nodes": nodes, "pageInfo": {"endCursor": None, "hasNextPage": False}}
            return {"repository": {"defaultBranchRef": {"target": {"history": history}}}}
        raise AssertionError(f"unexpected query: {query}")


class FixedClock:
    def today(self):
        return TODAY


def svg_texts(path):
    return list(ET.fromstring(path.read_text(encoding="utf-8")).iter("{http://www.w3.org/2000/svg}text"))


def svg_text(path):
    return ["".join(element.itertext()) for element in svg_texts(path)]


class BuildRefreshTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.root = Path(self._directory.name)
        (self.root / "assets").mkdir()
        (self.root / "assets" / "ascii-dark.txt").write_text("  @@\n @@@@\n", encoding="utf-8")
        (self.root / "assets" / "ascii-light.txt").write_text("  ##\n ####\n", encoding="utf-8")
        (self.root / "profile.json").write_text(json.dumps(PROFILE), encoding="utf-8")
        self.github = GitHubDouble()

    def tearDown(self):
        self._directory.cleanup()

    def refresh(self):
        build_refresh(self.root, self.github, FixedClock()).execute("NOTB4D")

    def test_writes_dark_and_light_cards_with_todays_numbers(self):
        self.refresh()

        dark = svg_text(self.root / "dark_mode.svg")
        light = svg_text(self.root / "light_mode.svg")
        self.assertEqual(dark[:2], ["  @@", " @@@@"])
        self.assertEqual(light[:2], ["  ##", " ####"])
        self.assertEqual(dark[2:], light[2:])
        card = "\n".join(dark[2:])
        self.assertRegex(card, r"Uptime: \.+ 5 years, 10 months, 28 days")
        self.assertRegex(card, r"Repos: \.+ 2 \{Contributed: 3\} \| Stars: \.+ 3")
        self.assertRegex(card, r"Commits: \.+ 4 \| Followers: \.+ 17")
        self.assertRegex(card, r"Lines of Code on GitHub: \.+ 10,600 \( 12,500\+\+, 1,900-- \)")

    def test_draws_the_portrait_at_twelve_pixels(self):
        self.refresh()

        for name in ("dark_mode.svg", "light_mode.svg"):
            portrait = svg_texts(self.root / name)[:2]
            self.assertEqual({element.get("font-size") for element in portrait}, {"12px"})

    def test_recounts_nothing_when_no_repository_changed(self):
        self.refresh()
        counted = self.github.history_requests

        self.refresh()

        self.assertEqual(counted, 3)
        self.assertEqual(self.github.history_requests, counted)
        self.assertTrue((self.root / "cache" / "contributions.txt").exists())


if __name__ == "__main__":
    unittest.main()
