"""Helpers for every lab's ``demo.py``: start the server, drive a browser, save screenshots.

A demo is the recorded proof that a lab runs. It prints what travelled over
the wire and saves PNG screenshots next to the lab README. Screenshots need
Playwright (``pip install playwright`` then ``python -m playwright install
chromium``); without it the demo still prints its terminal output.
"""

from __future__ import annotations

import os
import shutil
import socket
import sys
import textwrap
from contextlib import contextmanager
from pathlib import Path

os.environ.setdefault("GENUX_STREAM_DELAY", "0.004")


def free_port() -> int:
    with socket.socket() as s:
        s.bind(("127.0.0.1", 0))
        return s.getsockname()[1]


def banner(title: str):
    print("=" * 72)
    print(title)
    print("=" * 72)


def show(label: str, text: str, width: int = 100, max_lines: int = 12):
    """Print a labelled, truncated block (keeps demo output under ~40 lines)."""
    lines = []
    for raw in str(text).splitlines() or [""]:
        lines += textwrap.wrap(raw, width) or [""]
    extra = len(lines) - max_lines
    print(f"--- {label}")
    for line in lines[:max_lines]:
        print("  " + line)
    if extra > 0:
        print(f"  ... ({extra} more lines)")


def _launch(p):
    try:
        return p.chromium.launch()
    except Exception:
        for exe in ("google-chrome", "chromium", "chromium-browser", "msedge"):
            path = shutil.which(exe)
            if path:
                return p.chromium.launch(executable_path=path)
        raise


@contextmanager
def browser_page(width: int = 1280, height: int = 860):
    """Yield a Playwright page, or None if Playwright/Chromium is unavailable."""
    try:
        from playwright.sync_api import sync_playwright
    except ImportError:
        print("(playwright not installed: screenshots skipped)")
        yield None
        return
    with sync_playwright() as p:
        try:
            browser = _launch(p)
        except Exception as exc:
            print(f"(no browser available: screenshots skipped - {exc.__class__.__name__})")
            yield None
            return
        page = browser.new_page(viewport={"width": width, "height": height}, device_scale_factor=1)
        page.on("pageerror", lambda e: print(f"[page error] {e}", file=sys.stderr))
        try:
            yield page
        finally:
            browser.close()


def snap(page, lab_dir: Path, name: str, full_page: bool = True):
    path = Path(lab_dir) / name
    page.screenshot(path=str(path), full_page=full_page)
    print(f"screenshot: {path.name}")
    return path


def inner_frame(page, selector: str = "iframe.genux-sandbox", index: int = 0):
    """The Playwright Frame object for a sandboxed iframe (to click inside it)."""
    page.wait_for_selector(selector)
    handle = page.query_selector_all(selector)[index]
    return handle.content_frame()


# ---------------------------------------------------------------- wire helpers
import json as _json
import urllib.request as _urlreq


def start(app):
    """Start a lab App on a free port in a background thread; return its base URL."""
    srv = app.serve(free_port(), block=False, quiet=True)
    return f"http://127.0.0.1:{srv.server_address[1]}"


def post(url: str, body) -> str:
    req = _urlreq.Request(url, data=_json.dumps(body).encode(), headers={"Content-Type": "application/json"})
    with _urlreq.urlopen(req, timeout=60) as r:
        return r.read().decode("utf-8")


def post_sse(url: str, body) -> list:
    from .web import read_sse

    return read_sse(post(url, body))


def agui_input(text: str, thread: str = "demo", messages=None, state=None, tools=None, forwarded=None) -> dict:
    return {
        "threadId": thread, "runId": f"run_{free_port()}",
        "messages": messages if messages is not None else [{"id": "u1", "role": "user", "content": text}],
        "state": state or {}, "tools": tools or [], "context": [], "forwardedProps": forwarded or {},
    }


def compact(obj, limit: int = 110) -> str:
    text = _json.dumps(obj, separators=(",", ":"))
    return text if len(text) <= limit else text[: limit - 3] + "..."
