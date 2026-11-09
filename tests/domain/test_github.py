import unittest

from profile_card.domain.github import Contribution, Repository


class RepositoryTests(unittest.TestCase):
    def test_owner_is_the_login_before_the_slash(self):
        self.assertEqual(Repository("Mobven/IAPKit", stars=3, commit_count=10).owner, "Mobven")

    def test_is_owned_by_a_login_regardless_of_case(self):
        repository = Repository("NOTB4D/QuizApp", stars=0, commit_count=5)

        self.assertTrue(repository.is_owned_by("notb4d"))
        self.assertFalse(repository.is_owned_by("Mobven"))


class ContributionTests(unittest.TestCase):
    def test_none_is_an_empty_contribution(self):
        self.assertEqual(Contribution.none(), Contribution(commits=0, additions=0, deletions=0))


if __name__ == "__main__":
    unittest.main()
