import os
import unittest
from unittest.mock import patch

from web.app import MAX_JSON_BODY_BYTES, application
from web.config import WebSettings


class WebApplicationTests(unittest.TestCase):
    def test_health_and_static_index_contracts(self):
        health = application.handle("GET", "/api/health")
        index = application.handle("GET", "/")
        self.assertEqual(200, health.status)
        self.assertEqual({"status": "ok"}, __import__("json").loads(health.body))
        self.assertEqual(200, index.status)
        self.assertIn(b"v0.2.1", index.body)
        self.assertNotIn(b"__FM26_VERSION__", index.body)

    def test_static_allowlist_blocks_arbitrary_and_traversal_paths(self):
        self.assertEqual(404, application.handle("GET", "/../fm26lab.py").status)
        self.assertEqual(404, application.handle("GET", "/role_catalog.json").status)
        self.assertEqual(405, application.handle("POST", "/app.js", b"{}").status)

    def test_api_errors_are_consistent_and_do_not_expose_exceptions(self):
        for response in (
            application.handle("PUT", "/api/health"),
            application.handle("POST", "/api/analyze", b"not json"),
            application.handle("POST", "/api/analyze", b"[]"),
            application.handle("POST", "/api/analyze", b"x" * (MAX_JSON_BODY_BYTES + 1)),
        ):
            payload = __import__("json").loads(response.body)
            self.assertIn("error", payload)
            self.assertEqual({"code", "message"}, set(payload["error"]))
            self.assertNotIn("Traceback", payload["error"]["message"])

    def test_environment_configuration_uses_safe_defaults_and_port(self):
        with patch.dict(os.environ, {"HOST": "0.0.0.0", "PORT": "9123", "WEB_DEBUG": "1"}, clear=False):
            settings = WebSettings.from_environment()
        self.assertEqual(("0.0.0.0", 9123, True), (settings.host, settings.port, settings.development))
        with patch.dict(os.environ, {"PORT": "70000"}, clear=False):
            with self.assertRaises(ValueError):
                WebSettings.from_environment()

    def test_team_instruction_endpoints(self):
        catalogue = __import__("json").loads(application.handle("GET", "/api/team-instructions?phase=IP").body)
        self.assertEqual({"IP"}, set(catalogue))
        self.assertEqual(18, len(catalogue["IP"]))
        self.assertEqual(200, application.handle("GET", "/api/sample-team-instructions").status)

    def test_workspace_is_pitch_and_instruction_focused(self):
        index = application.handle("GET", "/").body.decode("utf-8")
        self.assertNotIn("레스터 예시 불러오기", index)
        self.assertNotIn("PLAYER / ROLE INSPECTOR", index)
        self.assertIn("id=\"pitch\"", index)
        self.assertIn("id=\"evaluation\"", index)
        self.assertIn("팀 지침", index)


if __name__ == "__main__":
    unittest.main()
