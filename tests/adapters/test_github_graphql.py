import unittest

from profile_card.adapters.github_graphql import (
    GraphQLCommitHistory,
    GraphQLRepositoryCatalog,
    GraphQLUserDirectory,
)
from profile_card.domain.github import Contribution, GitHubUser, Repository


class ScriptedTransport:
    def __init__(self, *responses):
        self._responses = list(responses)
        self.variables: list[dict] = []

    def execute(self, query, variables):
        self.variables.append(dict(variables))
        return self._responses.pop(0)


def repository_page(nodes, next_cursor=None):
    return {
        "user": {
            "repositories": {
                "nodes": nodes,
                "pageInfo": {"endCursor": next_cursor, "hasNextPage": next_cursor is not None},
            }
        }
    }


def repository_node(name, stars, commits):
    branch = None if commits is None else {"target": {"history": {"totalCount": commits}}}
    return {"nameWithOwner": name, "stargazers": {"totalCount": stars}, "defaultBranchRef": branch}


def history_page(commits, next_cursor=None):
    return {
        "repository": {
            "defaultBranchRef": {
                "target": {
                    "history": {
                        "nodes": commits,
                        "pageInfo": {"endCursor": next_cursor, "hasNextPage": next_cursor is not None},
                    }
                }
            }
        }
    }


def commit(author_id, additions, deletions):
    author = {"user": None if author_id is None else {"id": author_id}}
    return {"additions": additions, "deletions": deletions, "author": author}


class GraphQLUserDirectoryTests(unittest.TestCase):
    def test_finds_the_users_id_and_follower_count(self):
        transport = ScriptedTransport({"user": {"id": "U1", "followers": {"totalCount": 17}}})

        user = GraphQLUserDirectory(transport).find("NOTB4D")

        self.assertEqual(user, GitHubUser(id="U1", followers=17))
        self.assertEqual(transport.variables, [{"login": "NOTB4D"}])

    def test_reports_an_unknown_login(self):
        transport = ScriptedTransport({"user": None})

        with self.assertRaises(LookupError):
            GraphQLUserDirectory(transport).find("nobody")


class GraphQLRepositoryCatalogTests(unittest.TestCase):
    def test_lists_repositories_with_stars_and_default_branch_commit_counts(self):
        transport = ScriptedTransport(
            repository_page(
                [repository_node("NOTB4D/QuizApp", 2, 12), repository_node("NOTB4D/Empty", 0, None)]
            )
        )

        repositories = GraphQLRepositoryCatalog(transport).repositories_of("NOTB4D")

        self.assertEqual(
            repositories,
            [Repository("NOTB4D/QuizApp", stars=2, commit_count=12), Repository("NOTB4D/Empty", 0, 0)],
        )

    def test_requests_owned_collaborated_and_organization_repositories(self):
        transport = ScriptedTransport(repository_page([]))

        GraphQLRepositoryCatalog(transport).repositories_of("NOTB4D")

        self.assertEqual(
            transport.variables,
            [
                {
                    "login": "NOTB4D",
                    "affiliations": ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"],
                    "cursor": None,
                }
            ],
        )

    def test_follows_pagination_cursors(self):
        transport = ScriptedTransport(
            repository_page([repository_node("NOTB4D/A", 0, 1)], next_cursor="C1"),
            repository_page([repository_node("Mobven/B", 5, 9)]),
        )

        repositories = GraphQLRepositoryCatalog(transport).repositories_of("NOTB4D")

        self.assertEqual([r.name_with_owner for r in repositories], ["NOTB4D/A", "Mobven/B"])
        self.assertEqual([v["cursor"] for v in transport.variables], [None, "C1"])

    def test_skips_inaccessible_repositories(self):
        transport = ScriptedTransport(repository_page([None, repository_node("NOTB4D/A", 0, 1)]))

        repositories = GraphQLRepositoryCatalog(transport).repositories_of("NOTB4D")

        self.assertEqual([r.name_with_owner for r in repositories], ["NOTB4D/A"])

    def test_counts_no_commits_when_the_default_branch_is_not_a_commit(self):
        node = {"nameWithOwner": "NOTB4D/A", "stargazers": {"totalCount": 0}, "defaultBranchRef": {"target": {}}}
        transport = ScriptedTransport(repository_page([node]))

        repositories = GraphQLRepositoryCatalog(transport).repositories_of("NOTB4D")

        self.assertEqual(repositories[0].commit_count, 0)


class GraphQLCommitHistoryTests(unittest.TestCase):
    QUIZ = Repository("NOTB4D/QuizApp", stars=0, commit_count=4)

    def test_counts_only_commits_authored_by_the_user(self):
        transport = ScriptedTransport(
            history_page([commit("U1", 10, 2), commit("U2", 5, 1), commit(None, 3, 3), commit("U1", 1, 1)])
        )

        contribution = GraphQLCommitHistory(transport).contribution_to(self.QUIZ, "U1")

        self.assertEqual(contribution, Contribution(commits=2, additions=11, deletions=3))

    def test_queries_the_repository_by_owner_and_name(self):
        transport = ScriptedTransport(history_page([]))

        GraphQLCommitHistory(transport).contribution_to(self.QUIZ, "U1")

        self.assertEqual(transport.variables, [{"owner": "NOTB4D", "name": "QuizApp", "cursor": None}])

    def test_follows_history_pagination(self):
        transport = ScriptedTransport(
            history_page([commit("U1", 10, 2)], next_cursor="H1"),
            history_page([commit("U1", 4, 4)]),
        )

        contribution = GraphQLCommitHistory(transport).contribution_to(self.QUIZ, "U1")

        self.assertEqual(contribution, Contribution(commits=2, additions=14, deletions=6))
        self.assertEqual([v["cursor"] for v in transport.variables], [None, "H1"])

    def test_returns_no_contribution_for_a_repository_without_a_default_branch(self):
        transport = ScriptedTransport({"repository": {"defaultBranchRef": None}})

        self.assertEqual(GraphQLCommitHistory(transport).contribution_to(self.QUIZ, "U1"), Contribution.none())

    def test_returns_no_contribution_for_an_inaccessible_repository(self):
        transport = ScriptedTransport({"repository": None})

        self.assertEqual(GraphQLCommitHistory(transport).contribution_to(self.QUIZ, "U1"), Contribution.none())


if __name__ == "__main__":
    unittest.main()
