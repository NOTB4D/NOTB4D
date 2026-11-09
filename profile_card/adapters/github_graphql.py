"""GitHub GraphQL API (v4) implementations of the user, repository and commit history ports."""

from collections.abc import Iterator
from typing import Any, Protocol

from profile_card.domain.github import Contribution, GitHubUser, Repository

AFFILIATIONS = ["OWNER", "COLLABORATOR", "ORGANIZATION_MEMBER"]

USER_QUERY = """
query($login: String!) {
  user(login: $login) {
    id
    followers {
      totalCount
    }
  }
}
"""

# 60 per page: larger pages that also count commit history tend to time out (HTTP 502).
REPOSITORIES_QUERY = """
query($login: String!, $affiliations: [RepositoryAffiliation], $cursor: String) {
  user(login: $login) {
    repositories(first: 60, after: $cursor, ownerAffiliations: $affiliations) {
      nodes {
        nameWithOwner
        stargazers {
          totalCount
        }
        defaultBranchRef {
          target {
            ... on Commit {
              history {
                totalCount
              }
            }
          }
        }
      }
      pageInfo {
        endCursor
        hasNextPage
      }
    }
  }
}
"""

HISTORY_QUERY = """
query($owner: String!, $name: String!, $cursor: String) {
  repository(owner: $owner, name: $name) {
    defaultBranchRef {
      target {
        ... on Commit {
          history(first: 100, after: $cursor) {
            nodes {
              additions
              deletions
              author {
                user {
                  id
                }
              }
            }
            pageInfo {
              endCursor
              hasNextPage
            }
          }
        }
      }
    }
  }
}
"""


class GraphQLTransport(Protocol):
    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        """Runs a query and returns its `data` object."""
        ...


class GraphQLUserDirectory:
    def __init__(self, transport: GraphQLTransport):
        self._transport = transport

    def find(self, login: str) -> GitHubUser:
        user = self._transport.execute(USER_QUERY, {"login": login})["user"]
        if user is None:
            raise LookupError(f"GitHub user {login!r} was not found")
        return GitHubUser(id=user["id"], followers=user["followers"]["totalCount"])


class GraphQLRepositoryCatalog:
    def __init__(self, transport: GraphQLTransport):
        self._transport = transport

    def repositories_of(self, login: str) -> list[Repository]:
        return [
            Repository(
                name_with_owner=node["nameWithOwner"],
                stars=node["stargazers"]["totalCount"],
                commit_count=_default_branch_commit_count(node),
            )
            for node in self._nodes(login)
            if node is not None
        ]

    def _nodes(self, login: str) -> Iterator[dict[str, Any] | None]:
        variables = {"login": login, "affiliations": AFFILIATIONS, "cursor": None}
        while True:
            connection = self._transport.execute(REPOSITORIES_QUERY, variables)["user"]["repositories"]
            yield from connection["nodes"]
            if not connection["pageInfo"]["hasNextPage"]:
                return
            variables = {**variables, "cursor": connection["pageInfo"]["endCursor"]}


class GraphQLCommitHistory:
    def __init__(self, transport: GraphQLTransport):
        self._transport = transport

    def contribution_to(self, repository: Repository, author_id: str) -> Contribution:
        commits = additions = deletions = 0
        for commit in self._commits(repository):
            if _author_id(commit) == author_id:
                commits += 1
                additions += commit["additions"]
                deletions += commit["deletions"]
        return Contribution(commits=commits, additions=additions, deletions=deletions)

    def _commits(self, repository: Repository) -> Iterator[dict[str, Any]]:
        owner, name = repository.name_with_owner.split("/", 1)
        variables = {"owner": owner, "name": name, "cursor": None}
        while True:
            response = self._transport.execute(HISTORY_QUERY, variables)
            history = _default_branch_history(response["repository"])
            if history is None:
                return
            yield from history["nodes"]
            if not history["pageInfo"]["hasNextPage"]:
                return
            variables = {**variables, "cursor": history["pageInfo"]["endCursor"]}


def _default_branch_commit_count(repository: dict[str, Any]) -> int:
    history = _default_branch_history(repository)
    return history["totalCount"] if history else 0


def _default_branch_history(repository: dict[str, Any] | None) -> dict[str, Any] | None:
    """The default branch's commit history, or None for empty or inaccessible repositories."""
    branch = (repository or {}).get("defaultBranchRef") or {}
    return (branch.get("target") or {}).get("history")


def _author_id(commit: dict[str, Any]) -> str | None:
    return (((commit.get("author") or {}).get("user")) or {}).get("id")
