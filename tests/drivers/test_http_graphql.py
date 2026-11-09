import json
import threading
import unittest
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer

from profile_card.drivers.http_graphql import GraphQLError, UrllibGraphQLTransport


class GitHubLikeServer:
    """Serves queued (status, payload) responses and records the requests it receives."""

    def __init__(self):
        self.responses: list[tuple[int, dict]] = []
        self.requests: list[dict] = []
        server = self

        class Handler(BaseHTTPRequestHandler):
            def do_POST(self):
                body = self.rfile.read(int(self.headers["Content-Length"]))
                server.requests.append({"path": self.path, "headers": self.headers, "body": json.loads(body)})
                status, payload = server.responses.pop(0)
                data = json.dumps(payload).encode()
                self.send_response(status)
                self.send_header("Content-Type", "application/json")
                self.send_header("Content-Length", str(len(data)))
                self.end_headers()
                self.wfile.write(data)

            def log_message(self, *args):
                pass

        self._http = ThreadingHTTPServer(("127.0.0.1", 0), Handler)
        self.url = f"http://127.0.0.1:{self._http.server_port}/graphql"
        threading.Thread(target=self._http.serve_forever, kwargs={"poll_interval": 0.01}, daemon=True).start()

    def close(self):
        self._http.shutdown()
        self._http.server_close()


class UrllibGraphQLTransportTests(unittest.TestCase):
    def setUp(self):
        self.server = GitHubLikeServer()
        self.warnings: list[str] = []
        self.transport = UrllibGraphQLTransport("secret-token", endpoint=self.server.url, warn=self.warnings.append)

    def tearDown(self):
        self.server.close()

    def test_posts_the_query_with_a_bearer_token_and_returns_its_data(self):
        self.server.responses.append((200, {"data": {"user": {"id": "U1"}}}))

        data = self.transport.execute("query { viewer { id } }", {"login": "NOTB4D"})

        self.assertEqual(data, {"user": {"id": "U1"}})
        request = self.server.requests[0]
        self.assertEqual(request["body"], {"query": "query { viewer { id } }", "variables": {"login": "NOTB4D"}})
        self.assertEqual(request["headers"]["Authorization"], "bearer secret-token")
        self.assertEqual(request["headers"]["Content-Type"], "application/json")
        self.assertTrue(request["headers"]["User-Agent"])

    def test_returns_partial_data_and_warns_about_its_errors(self):
        errors = [{"type": "FORBIDDEN", "message": "Resource protected by organization SAML enforcement."}]
        self.server.responses.append((200, {"data": {"user": None}, "errors": errors}))

        data = self.transport.execute("query { x }", {})

        self.assertEqual(data, {"user": None})
        self.assertEqual(len(self.warnings), 1)
        self.assertIn("SAML enforcement", self.warnings[0])

    def test_fails_when_the_response_carries_no_data(self):
        self.server.responses.append((200, {"errors": [{"message": "Bad credentials"}]}))

        with self.assertRaisesRegex(GraphQLError, "Bad credentials"):
            self.transport.execute("query { x }", {})

    def test_fails_with_the_status_of_an_http_error(self):
        self.server.responses.append((502, {"message": "Server Error"}))

        with self.assertRaisesRegex(GraphQLError, "502"):
            self.transport.execute("query { x }", {})


if __name__ == "__main__":
    unittest.main()
