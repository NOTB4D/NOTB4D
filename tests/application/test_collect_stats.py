import unittest

from profile_card.application.collect_stats import CollectGitHubStats
from profile_card.application.ports import CachedContribution
from profile_card.domain.github import Contribution, GitHubUser, Repository
from tests.application.fakes import (
    FakeCommitHistory,
    FakeContributionCache,
    FakeRepositoryCatalog,
    FakeUserDirectory,
)

USER = GitHubUser(id="MDQ6VXNlcjc1OTEyMjA2", followers=17)

QUIZ = Repository("NOTB4D/QuizApp", stars=2, commit_count=12)
WEATHER = Repository("NOTB4D/TheWeatherApp", stars=1, commit_count=30)
IAPKIT = Repository("Mobven/IAPKit", stars=40, commit_count=200)

CONTRIBUTIONS = {
    QUIZ.name_with_owner: Contribution(commits=12, additions=900, deletions=100),
    WEATHER.name_with_owner: Contribution(commits=25, additions=2_000, deletions=300),
    IAPKIT.name_with_owner: Contribution(commits=60, additions=5_000, deletions=1_200),
}


def collector(repositories, history=None, cache=None, user=USER):
    return CollectGitHubStats(
        users=FakeUserDirectory(user),
        catalog=FakeRepositoryCatalog(repositories),
        history=history or FakeCommitHistory(CONTRIBUTIONS),
        cache=cache or FakeContributionCache(),
    )


class RepositoryCountTests(unittest.TestCase):
    def test_counts_owned_repositories_and_all_contributed_repositories(self):
        stats = collector([QUIZ, WEATHER, IAPKIT]).collect("NOTB4D")

        self.assertEqual(stats.repositories, 2)
        self.assertEqual(stats.contributed_repositories, 3)

    def test_counts_stars_of_owned_repositories_only(self):
        stats = collector([QUIZ, WEATHER, IAPKIT]).collect("NOTB4D")

        self.assertEqual(stats.stars, 3)

    def test_matches_the_owner_login_case_insensitively(self):
        stats = collector([QUIZ, WEATHER]).collect("notb4d")

        self.assertEqual(stats.repositories, 2)

    def test_takes_followers_from_the_user(self):
        users = FakeUserDirectory(USER)
        use_case = CollectGitHubStats(
            users=users,
            catalog=FakeRepositoryCatalog([]),
            history=FakeCommitHistory({}),
            cache=FakeContributionCache(),
        )

        stats = use_case.collect("NOTB4D")

        self.assertEqual(stats.followers, 17)
        self.assertEqual(users.requested_logins, ["NOTB4D"])


class ContributionTallyTests(unittest.TestCase):
    def test_sums_the_users_commits_and_lines_across_all_repositories(self):
        stats = collector([QUIZ, WEATHER, IAPKIT]).collect("NOTB4D")

        self.assertEqual(stats.commits, 97)
        self.assertEqual(stats.lines_added, 7_900)
        self.assertEqual(stats.lines_deleted, 1_600)

    def test_asks_history_for_the_users_own_commits(self):
        history = FakeCommitHistory(CONTRIBUTIONS)

        collector([QUIZ], history=history).collect("NOTB4D")

        self.assertEqual(history.requests, [(QUIZ.name_with_owner, USER.id)])

    def test_skips_history_of_repositories_without_commits(self):
        empty = Repository("NOTB4D/Empty", stars=0, commit_count=0)
        history = FakeCommitHistory(CONTRIBUTIONS)

        stats = collector([empty], history=history).collect("NOTB4D")

        self.assertEqual(history.requests, [])
        self.assertEqual(stats.commits, 0)


class ContributionCacheTests(unittest.TestCase):
    def test_reuses_a_cached_contribution_while_the_commit_count_is_unchanged(self):
        cached = CachedContribution(commit_count=12, contribution=Contribution(10, 500, 50))
        cache = FakeContributionCache({QUIZ.name_with_owner: cached})
        history = FakeCommitHistory(CONTRIBUTIONS)

        stats = collector([QUIZ], history=history, cache=cache).collect("NOTB4D")

        self.assertEqual(history.requests, [])
        self.assertEqual((stats.commits, stats.lines_added, stats.lines_deleted), (10, 500, 50))

    def test_recounts_a_repository_whose_commit_count_changed(self):
        stale = CachedContribution(commit_count=11, contribution=Contribution(10, 500, 50))
        cache = FakeContributionCache({QUIZ.name_with_owner: stale})

        stats = collector([QUIZ], cache=cache).collect("NOTB4D")

        self.assertEqual(stats.commits, 12)
        self.assertEqual(
            cache.saved[QUIZ.name_with_owner],
            CachedContribution(commit_count=12, contribution=CONTRIBUTIONS[QUIZ.name_with_owner]),
        )

    def test_saves_only_repositories_that_still_exist(self):
        gone = CachedContribution(commit_count=3, contribution=Contribution(3, 30, 3))
        cache = FakeContributionCache({"NOTB4D/Deleted": gone})

        collector([QUIZ], cache=cache).collect("NOTB4D")

        self.assertEqual(set(cache.saved), {QUIZ.name_with_owner})

    def test_keeps_counted_and_cached_progress_when_history_fails(self):
        cached_iapkit = CachedContribution(commit_count=199, contribution=Contribution(59, 4_900, 1_100))
        cache = FakeContributionCache({IAPKIT.name_with_owner: cached_iapkit})
        history = FakeCommitHistory(CONTRIBUTIONS, failing={WEATHER.name_with_owner})

        with self.assertRaises(RuntimeError):
            collector([QUIZ, WEATHER, IAPKIT], history=history, cache=cache).collect("NOTB4D")

        self.assertEqual(
            cache.saved,
            {
                QUIZ.name_with_owner: CachedContribution(12, CONTRIBUTIONS[QUIZ.name_with_owner]),
                IAPKIT.name_with_owner: cached_iapkit,
            },
        )


if __name__ == "__main__":
    unittest.main()
