"""Server-side helpers for the MCP Apps labs.

An MCP App is three additions to a normal MCP server (SEP-1865):

1. a **resource** with a ``ui://`` URI and MIME type ``text/html;profile=mcp-app``
   whose text is a complete HTML document (the *view*);
2. a **tool** whose ``_meta.ui.resourceUri`` points at that resource
   (``_meta.ui.visibility`` says whether the model, the app, or both may call it);
3. a **tool result** with ``content`` (text, for the model and for hosts without UI)
   and ``structuredContent`` (data, for the view).

The view must be self-contained (the host renders it from a string), so
``build_view`` inlines the bridge, the shared CSS and the component kit.
"""

from __future__ import annotations

import json
from pathlib import Path

from mcp import types

SHARED = Path(__file__).resolve().parent
ROOT = SHARED.parents[1]
MIME = "text/html;profile=mcp-app"
# No network for the view, no external resources. A view that needs a CDN would list it here.
VIEW_META = {"ui": {"csp": {"connectDomains": [], "resourceDomains": []}, "prefersBorder": True}}


def build_view(view_file: Path) -> str:
    html = Path(view_file).read_text(encoding="utf-8")
    inline = {
        "<!-- genux:style -->": "<style>" + (ROOT / "common" / "web" / "style.css").read_text(encoding="utf-8") + "</style>",
        "<!-- genux:bridge -->": "<script>" + (SHARED / "view-bridge.js").read_text(encoding="utf-8") + "</script>",
        "<!-- genux:kit -->": "<script>" + (SHARED / "view-kit.js").read_text(encoding="utf-8") + "</script>",
    }
    for marker, code in inline.items():
        html = html.replace(marker, code)
    return html


def ui_meta(resource_uri: str, visibility: list[str] | None = None) -> dict:
    meta = {"ui": {"resourceUri": resource_uri}}
    if visibility:
        meta["ui"]["visibility"] = visibility
    return meta


def result(text: str, data: dict) -> types.CallToolResult:
    """content for the model (and UI-less hosts), structuredContent for the view."""
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], structured_content=data)


def dump(obj) -> dict:
    return json.loads(obj.model_dump_json(by_alias=True, exclude_none=True))


def official_check(bridge_log: list) -> dict | None:
    """Validate recorded bridge messages with @modelcontextprotocol/ext-apps (None without Node)."""
    import shutil
    import subprocess

    if not shutil.which("node") or not (ROOT / "node_modules" / "@modelcontextprotocol" / "ext-apps").exists():
        return None
    proc = subprocess.run(["node", str(SHARED / "conformance.mjs")], input=json.dumps(bridge_log), capture_output=True, text=True, timeout=60)
    return json.loads(proc.stdout) if proc.stdout.strip() else {"ok": False, "errors": [proc.stderr[-400:]]}
