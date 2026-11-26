"""A tiny HTTP server (standard library only) with JSON routes, SSE and static files.

Every lab's ``server.py`` builds an ``App``, registers a few routes and calls
``app.serve(port)``. Keeping the server this small means the walkthrough can
focus on the generative-UI part instead of a web framework.

Static files:
  /                -> <lab>/page/index.html
  /<file>          -> <lab>/page/<file>
  /common/<file>   -> common/web/<file>   (shared browser modules)
  /<mount>/<file>  -> any extra folder added with app.mount()
"""

from __future__ import annotations

import json
import mimetypes
import threading
from http.server import BaseHTTPRequestHandler, ThreadingHTTPServer
from pathlib import Path
from typing import Callable, Iterable
from urllib.parse import parse_qs, urlparse

COMMON_WEB = Path(__file__).parent / "web"
mimetypes.add_type("text/javascript", ".js")
mimetypes.add_type("text/javascript", ".mjs")


class Request:
    def __init__(self, method: str, path: str, query: dict, body: bytes, headers):
        self.method, self.path, self.query, self.body, self.headers = method, path, query, body, headers

    def json(self):
        return json.loads(self.body.decode("utf-8") or "null")


class Response:
    def __init__(self, body: str | bytes, status: int = 200, content_type: str = "text/plain; charset=utf-8"):
        self.body = body.encode("utf-8") if isinstance(body, str) else body
        self.status, self.content_type = status, content_type


class SSE:
    """Wrap an iterator of already-encoded SSE frames (``data: ...\\n\\n``)."""

    def __init__(self, frames: Iterable[str], content_type: str = "text/event-stream"):
        self.frames, self.content_type = frames, content_type


def sse_frame(obj, event: str | None = None) -> str:
    head = f"event: {event}\n" if event else ""
    return f"{head}data: {json.dumps(obj, separators=(',', ':'))}\n\n"


class App:
    def __init__(self, page_dir: str | Path, title: str = "genux lab"):
        self.page_dir = Path(page_dir)
        self.title = title
        self.routes: dict[tuple[str, str], Callable[[Request], object]] = {}
        self.mounts: dict[str, Path] = {"common": COMMON_WEB}

    # ---- registration -------------------------------------------------
    def route(self, method: str, path: str):
        def deco(fn):
            self.routes[(method.upper(), path)] = fn
            return fn

        return deco

    def get(self, path: str):
        return self.route("GET", path)

    def post(self, path: str):
        return self.route("POST", path)

    def mount(self, prefix: str, folder: str | Path):
        self.mounts[prefix.strip("/")] = Path(folder)

    # ---- serving ------------------------------------------------------
    def serve(self, port: int, block: bool = True, quiet: bool = False):
        app = self

        class Handler(BaseHTTPRequestHandler):
            protocol_version = "HTTP/1.1"

            def log_message(self, *args):  # keep demo output readable
                pass

            def _dispatch(self, method: str):
                url = urlparse(self.path)
                length = int(self.headers.get("Content-Length") or 0)
                body = self.rfile.read(length) if length else b""
                req = Request(method, url.path, {k: v[-1] for k, v in parse_qs(url.query).items()}, body, self.headers)
                handler = app.routes.get((method, url.path))
                try:
                    if handler is not None:
                        return self._send(handler(req))
                    if method == "GET":
                        return self._static(url.path)
                    return self._send(Response("not found", 404))
                except Exception as exc:  # surface errors to the page instead of hanging it
                    return self._send(Response(json.dumps({"error": f"{type(exc).__name__}: {exc}"}), 500, "application/json"))

            def do_GET(self):
                self._dispatch("GET")

            def do_POST(self):
                self._dispatch("POST")

            def _static(self, path: str):
                rel = path.lstrip("/") or "index.html"
                first, _, rest = rel.partition("/")
                base, rel = (app.mounts[first], rest) if first in app.mounts and rest else (app.page_dir, rel)
                target = (base / rel).resolve()
                if not str(target).startswith(str(base.resolve())) or not target.is_file():
                    return self._send(Response("not found", 404))
                ctype = mimetypes.guess_type(target.name)[0] or "application/octet-stream"
                if ctype.startswith("text/") or ctype.endswith("javascript") or ctype.endswith("json"):
                    ctype += "; charset=utf-8"
                self._send(Response(target.read_bytes(), 200, ctype))

            def _send(self, result):
                if isinstance(result, SSE):
                    self.send_response(200)
                    self.send_header("Content-Type", result.content_type)
                    self.send_header("Cache-Control", "no-cache")
                    self.send_header("Connection", "close")
                    self.end_headers()
                    try:
                        for frame in result.frames:
                            self.wfile.write(frame.encode("utf-8"))
                            self.wfile.flush()
                    except (BrokenPipeError, ConnectionResetError):
                        pass
                    self.close_connection = True
                    return
                if not isinstance(result, Response):
                    result = Response(json.dumps(result), 200, "application/json")
                self.send_response(result.status)
                self.send_header("Content-Type", result.content_type)
                self.send_header("Content-Length", str(len(result.body)))
                self.send_header("Cache-Control", "no-store")
                self.end_headers()
                self.wfile.write(result.body)

        server = ThreadingHTTPServer(("127.0.0.1", port), Handler)
        server.daemon_threads = True
        if not quiet:
            print(f"{self.title}: http://127.0.0.1:{server.server_address[1]}/", flush=True)
        if block:
            try:
                server.serve_forever()
            except KeyboardInterrupt:
                pass
            return server
        threading.Thread(target=server.serve_forever, daemon=True).start()
        return server


def read_sse(raw: str) -> list:
    """Parse an SSE body into a list of JSON payloads (used by tests and demos)."""
    out = []
    for block in raw.split("\n\n"):
        data = [line[5:].lstrip() for line in block.splitlines() if line.startswith("data:")]
        if data:
            out.append(json.loads("\n".join(data)))
    return out
