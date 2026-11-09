"""GraphQL transport over HTTPS using only the standard library."""

import json
import sys
import urllib.error
import urllib.request
from collections.abc import Callable
from typing import Any

GITHUB_GRAPHQL_ENDPOINT = "https://api.github.com/graphql"


class GraphQLError(RuntimeError):
    pass


def _warn_on_stderr(message: str) -> None:
    print(message, file=sys.stderr)


class UrllibGraphQLTransport:
    def __init__(
        self,
        token: str,
        endpoint: str = GITHUB_GRAPHQL_ENDPOINT,
        timeout_seconds: float = 60,
        warn: Callable[[str], None] = _warn_on_stderr,
    ):
        self._token = token
        self._endpoint = endpoint
        self._timeout_seconds = timeout_seconds
        self._warn = warn

    def execute(self, query: str, variables: dict[str, Any]) -> dict[str, Any]:
        request = urllib.request.Request(
            self._endpoint,
            data=json.dumps({"query": query, "variables": variables}).encode("utf-8"),
            method="POST",
            headers={
                "Authorization": f"bearer {self._token}",
                "Content-Type": "application/json",
                "User-Agent": "profile-card",
            },
        )
        try:
            with urllib.request.urlopen(request, timeout=self._timeout_seconds) as response:
                payload = json.load(response)
        except urllib.error.HTTPError as error:
            detail = error.read().decode("utf-8", errors="replace")[:500]
            raise GraphQLError(f"GitHub GraphQL request failed with HTTP {error.code}: {detail}") from error

        errors = payload.get("errors")
        if payload.get("data") is None:
            raise GraphQLError(f"GitHub GraphQL returned no data: {errors}")
        if errors:
            self._warn(f"GitHub GraphQL returned partial data with errors: {errors}")
        return payload["data"]
