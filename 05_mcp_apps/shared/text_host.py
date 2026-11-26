"""A host WITHOUT UI support - the fallback every MCP App must survive.

Many MCP clients (CLIs, older hosts, coding harnesses) do not render UI
resources. They ignore ``_meta.ui`` and show the tool result's ``content``.
That is why every MCP App tool returns meaningful text in ``content`` next to
``structuredContent``: "ship both".

    python text_host.py ../lab4_mixed/server.py coffee_dashboard_hybrid '{"request": "dashboard"}'
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parent))

from host import McpConnection  # noqa: E402


def run(server: Path, tool: str, arguments: dict) -> str:
    conn = McpConnection(Path(server))
    visible = [t for t in conn.tools() if "model" in (((t.get("_meta") or {}).get("ui") or {}).get("visibility") or ["model"])]
    lines = [f"[text host] tools offered to the model: {', '.join(t['name'] for t in visible)}"]
    res = conn.call(tool, arguments)
    lines.append(f"[text host] {tool} -> (UI resource ignored, showing content[])")
    lines += ["    " + l for block in res["content"] if block["type"] == "text" for l in block["text"].splitlines()]
    return "\n".join(lines)


if __name__ == "__main__":
    print(run(Path(sys.argv[1]), sys.argv[2], json.loads(sys.argv[3]) if len(sys.argv) > 3 else {}))
