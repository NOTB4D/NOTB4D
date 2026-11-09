import unittest

from profile_card.domain.stats import GitHubStats


class GitHubStatsTests(unittest.TestCase):
    def test_net_lines_are_additions_minus_deletions(self):
        stats = GitHubStats(
            repositories=26,
            contributed_repositories=30,
            stars=7,
            commits=1234,
            followers=17,
            lines_added=150_000,
            lines_deleted=26_544,
        )

        self.assertEqual(stats.net_lines, 123_456)


if __name__ == "__main__":
    unittest.main()
