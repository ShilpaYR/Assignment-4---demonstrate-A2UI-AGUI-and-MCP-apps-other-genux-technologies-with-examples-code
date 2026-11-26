"""Policy for open-ended (model-written) HTML.

Open-ended generation means the model writes markup and script. The labs
never trust it. Three layers, applied in this order:

1. ``check_html`` (server side): reject documents that are too large or
   reach for the network (external scripts, stylesheets, fetch to a URL).
2. A Content-Security-Policy injected as the *first* element of <head>, so
   nothing in the document runs before the policy is in force.
3. A sandboxed iframe (``sandbox="allow-scripts"``, no ``allow-same-origin``)
   on the page. The document runs in an opaque origin: no cookies, no
   storage, no access to the parent DOM. Its only way out is
   ``postMessage`` with one accepted shape (``genux:event``).

The browser half of this lives in ``common/web/sandbox.js``.
"""

from __future__ import annotations

import re

CSP = (
    "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; "
    "img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'"
)
MAX_BYTES = 60_000

_EXTERNAL = [
    (re.compile(r"<script[^>]+\bsrc\s*=", re.I), "external <script src> is not allowed"),
    (re.compile(r"<link[^>]+\bhref\s*=\s*[\"']?(https?:)?//", re.I), "external stylesheet is not allowed"),
    (re.compile(r"\b(fetch|XMLHttpRequest|WebSocket|EventSource)\s*\(", re.I), "network APIs are not allowed"),
    (re.compile(r"<(iframe|object|embed)\b", re.I), "nested frames/plugins are not allowed"),
    (re.compile(r"\bsrc\s*=\s*[\"']?https?://", re.I), "remote resources are not allowed"),
]


def check_html(html: str, max_bytes: int = MAX_BYTES) -> list[str]:
    """Return a list of policy problems; an empty list means the document may be mounted."""
    problems = []
    if not html or not html.strip():
        problems.append("document is empty")
    if len(html.encode("utf-8")) > max_bytes:
        problems.append(f"document is larger than {max_bytes} bytes")
    for pattern, message in _EXTERNAL:
        if pattern.search(html or ""):
            problems.append(message)
    return problems


def with_csp(html: str, csp: str = CSP) -> str:
    """Insert the CSP <meta> as the first child of <head> (creating <head> if needed)."""
    meta = f'<meta http-equiv="Content-Security-Policy" content="{csp}">'
    if re.search(r"<head[^>]*>", html, re.I):
        return re.sub(r"(<head[^>]*>)", lambda m: m.group(1) + meta, html, count=1, flags=re.I)
    if re.search(r"<html[^>]*>", html, re.I):
        return re.sub(r"(<html[^>]*>)", lambda m: m.group(1) + "<head>" + meta + "</head>", html, count=1, flags=re.I)
    return f"<!doctype html><html><head>{meta}</head><body>{html}</body></html>"
