"""HTTP/WSGI adapters for FM26 Tactical Lab; tactical work remains in core.pipeline."""
from __future__ import annotations

import argparse
import json
import mimetypes
from dataclasses import dataclass
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable
from urllib.parse import parse_qs, urlparse

from web import api
from web.config import WebSettings
from web.version import VERSION


STATIC = Path(__file__).resolve().parent / "static"
MAX_JSON_BODY_BYTES = 1_048_576
STATIC_ASSETS = {
    "/": "index.html",
    **{f"/{path.relative_to(STATIC).as_posix()}": path.relative_to(STATIC).as_posix()
       for path in STATIC.rglob("*") if path.is_file()},
}


@dataclass(frozen=True)
class Response:
    status: int
    content_type: str
    body: bytes
    headers: tuple[tuple[str, str], ...] = ()


class RequestError(ValueError):
    def __init__(self, status: int, code: str, message: str):
        self.status, self.code, self.message = status, code, message


def _json_response(status: int, payload: object) -> Response:
    return Response(status, "application/json; charset=utf-8", json.dumps(payload, ensure_ascii=False).encode("utf-8"))


def _error(status: int, code: str, message: str) -> Response:
    return _json_response(status, {"error": {"code": code, "message": message}})


def _read_json(body: bytes) -> object:
    if len(body) > MAX_JSON_BODY_BYTES:
        raise RequestError(413, "payload_too_large", "JSON request body is too large.")
    try:
        return json.loads(body.decode("utf-8"))
    except (UnicodeDecodeError, json.JSONDecodeError) as exc:
        raise RequestError(400, "malformed_json", "Request body must be valid UTF-8 JSON.") from exc


class WebApplication:
    """Framework-neutral request router used by both local HTTP and WSGI adapters."""

    def handle(self, method: str, target: str, body: bytes = b"") -> Response:
        parsed = urlparse(target)
        try:
            if parsed.path.startswith("/api/"):
                return self._api(method, parsed.path, parse_qs(parsed.query), body)
            if method not in ("GET", "HEAD"):
                return _error(405, "method_not_allowed", "Only GET and HEAD are allowed for static assets.")
            return self._static(parsed.path, head_only=method == "HEAD")
        except RequestError as exc:
            return _error(exc.status, exc.code, exc.message)
        except (TypeError, ValueError):
            return _error(400, "invalid_request", "Request parameters are invalid.")
        except Exception:
            # Do not expose implementation or local-path details to public clients.
            return _error(500, "internal_error", "The server could not complete the request.")

    def _api(self, method: str, path: str, query: dict[str, list[str]], body: bytes) -> Response:
        if method == "GET":
            if path == "/api/health":
                return _json_response(200, {"status": "ok"})
            if path == "/api/presets":
                return _json_response(200, api.formation_presets_payload())
            if path == "/api/pitch-layout":
                return _json_response(200, api.pitch_layout_payload_for_presets())
            if path == "/api/roles":
                count = query.get("centre_back_line_count", [None])[0]
                return _json_response(200, api.roles_payload(query.get("phase", [None])[0], query.get("position", [None])[0], int(count) if count else None))
            if path == "/api/sample":
                return _json_response(200, api.sample_tactic())
            if path == "/api/team-instructions":
                return _json_response(200, api.team_instructions_payload(query.get("phase", [None])[0]))
            if path == "/api/sample-team-instructions":
                return _json_response(200, api.sample_team_instructions_payload())
            return _error(404, "not_found", "API endpoint was not found.")
        if method == "POST" and path in ("/api/analyze", "/api/evidence-sufficiency"):
            payload = _read_json(body)
            handler = api.analyze_payload if path == "/api/analyze" else api.evidence_sufficiency_payload
            return _json_response(200, handler(payload))
        if method not in ("GET", "POST"):
            return _error(405, "method_not_allowed", "HTTP method is not allowed for this API endpoint.")
        return _error(404, "not_found", "API endpoint was not found.")

    def _static(self, path: str, head_only: bool) -> Response:
        filename = STATIC_ASSETS.get(path)
        if filename is None:
            return _error(404, "not_found", "Static asset was not found.")
        asset = STATIC / filename
        content = asset.read_bytes()
        if filename == "index.html":
            content = content.replace(b"__FM26_VERSION__", VERSION.encode("ascii"))
        content_type = mimetypes.guess_type(filename)[0] or "application/octet-stream"
        if content_type.startswith("text/") or filename.endswith(".js"):
            content_type += "; charset=utf-8"
        return Response(200, content_type, b"" if head_only else content)


application = WebApplication()


class LocalHandler(BaseHTTPRequestHandler):
    def _respond(self, body: bytes = b"") -> None:
        response = application.handle(self.command, self.path, body)
        self.send_response(response.status)
        self.send_header("Content-Type", response.content_type)
        self.send_header("Content-Length", str(len(response.body)))
        self.send_header("X-Content-Type-Options", "nosniff")
        for key, value in response.headers:
            self.send_header(key, value)
        self.end_headers()
        if self.command != "HEAD":
            self.wfile.write(response.body)

    def do_GET(self) -> None: self._respond()
    def do_HEAD(self) -> None: self._respond()

    def do_POST(self) -> None:
        try:
            size = int(self.headers.get("Content-Length", "0"))
        except ValueError:
            return self._respond(b"{")
        if size > MAX_JSON_BODY_BYTES:
            return self._respond(b"x" * (MAX_JSON_BODY_BYTES + 1))
        self._respond(self.rfile.read(max(0, size)))

    def do_PUT(self) -> None: self._respond()
    def do_DELETE(self) -> None: self._respond()
    def do_PATCH(self) -> None: self._respond()
    def do_OPTIONS(self) -> None: self._respond()

    def log_message(self, format: str, *args: object) -> None:
        # Keep local requests observable without emitting request bodies or tracebacks.
        super().log_message(format, *args)


def wsgi_application(environ: dict, start_response: Callable) -> list[bytes]:
    """Provider-neutral WSGI entry point; use a platform-selected WSGI server in production."""
    length = environ.get("CONTENT_LENGTH", "0") or "0"
    try:
        size = max(0, int(length))
    except ValueError:
        size = 0
    body = environ["wsgi.input"].read(min(size, MAX_JSON_BODY_BYTES + 1))
    target = environ.get("PATH_INFO", "/")
    if environ.get("QUERY_STRING"):
        target += "?" + environ["QUERY_STRING"]
    response = application.handle(environ.get("REQUEST_METHOD", "GET"), target, body)
    reason = {200: "OK", 400: "Bad Request", 404: "Not Found", 405: "Method Not Allowed", 413: "Payload Too Large", 500: "Internal Server Error"}.get(response.status, "OK")
    start_response(f"{response.status} {reason}", [("Content-Type", response.content_type), ("Content-Length", str(len(response.body))), ("X-Content-Type-Options", "nosniff"), *response.headers])
    return [response.body]


def main() -> None:
    settings = WebSettings.from_environment()
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", default=settings.host)
    parser.add_argument("--port", type=int, default=settings.port)
    args = parser.parse_args()
    server = ThreadingHTTPServer((args.host, args.port), LocalHandler)
    print(f"FM26 Tactical Lab Web MVP v{VERSION}: http://{args.host}:{args.port}")
    server.serve_forever()


if __name__ == "__main__":
    main()
