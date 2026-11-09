import tempfile
import unittest
from pathlib import Path

from profile_card.adapters.contribution_cache_file import FileContributionCache
from profile_card.application.ports import CachedContribution
from profile_card.domain.github import Contribution

QUIZ = "NOTB4D/QuizApp"
IAPKIT = "Mobven/IAPKit"
QUIZ_ENTRY = CachedContribution(commit_count=12, contribution=Contribution(12, 900, 100))
IAPKIT_ENTRY = CachedContribution(commit_count=200, contribution=Contribution(60, 5_000, 1_200))


class FileContributionCacheTests(unittest.TestCase):
    def setUp(self):
        self._directory = tempfile.TemporaryDirectory()
        self.path = Path(self._directory.name) / "cache" / "contributions.txt"

    def tearDown(self):
        self._directory.cleanup()

    def test_is_empty_before_anything_is_saved(self):
        self.assertEqual(FileContributionCache(self.path).load([QUIZ]), {})

    def test_returns_saved_entries_of_the_requested_repositories(self):
        FileContributionCache(self.path).save({QUIZ: QUIZ_ENTRY, IAPKIT: IAPKIT_ENTRY})

        loaded = FileContributionCache(self.path).load([QUIZ, "NOTB4D/Unknown"])

        self.assertEqual(loaded, {QUIZ: QUIZ_ENTRY})

    def test_does_not_reveal_repository_names(self):
        FileContributionCache(self.path).save({"Mobven/SecretApp": IAPKIT_ENTRY})

        text = self.path.read_text(encoding="utf-8")

        self.assertNotIn("SecretApp", text)
        self.assertNotIn("Mobven", text)

    def test_save_replaces_previous_entries(self):
        cache = FileContributionCache(self.path)
        cache.save({QUIZ: QUIZ_ENTRY})

        cache.save({IAPKIT: IAPKIT_ENTRY})

        self.assertEqual(cache.load([QUIZ, IAPKIT]), {IAPKIT: IAPKIT_ENTRY})

    def test_writes_the_same_file_for_the_same_entries(self):
        cache = FileContributionCache(self.path)
        cache.save({QUIZ: QUIZ_ENTRY, IAPKIT: IAPKIT_ENTRY})
        first = self.path.read_text(encoding="utf-8")

        cache.save({IAPKIT: IAPKIT_ENTRY, QUIZ: QUIZ_ENTRY})

        self.assertEqual(self.path.read_text(encoding="utf-8"), first)


if __name__ == "__main__":
    unittest.main()
