"""Part 5 / Lab 3 - MCP Apps, OPEN-ENDED mode: model-written HTML, two sandboxes deep.

``generate_widget(request)`` asks the server's own model for a complete HTML
widget, checks it against the HTML policy, and returns it in
``structuredContent.html``. The model key never leaves the server.

The view mounts that HTML in a **nested** sandboxed iframe with its own CSP:

    host page  ->  MCP App view (sandbox="allow-scripts", CSP from _meta.ui.csp)
               ->  generated widget (sandbox="allow-scripts", CSP injected first)

The widget can only ``genux.emit`` to the view; the view decides what reaches
the host - here ``ui/update-model-context`` (what the model will know on its
next turn) and ``ui/message``.

    python run_host.py           # http://127.0.0.1:8053
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from mcp import types  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402

from common import scenario, tokens  # noqa: E402
from common.llm import get_llm, strip_fences  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from mcpapps import MIME, VIEW_META, build_view, result, ui_meta  # noqa: E402

VIEW_URI = "ui://coffee/widget-host.html"
SYSTEM = ("Write ONE self-contained HTML document (inline CSS/JS only, no network). It runs in a sandbox; "
          "call genux.emit('apply_price', {price}) when the user picks a price. Output HTML only.")
server = MCPServer("coffee-cart-open-ended")
llm = get_llm(HERE / "fixtures")


@server.tool(meta=ui_meta(VIEW_URI, ["model", "app"]))
def generate_widget(request: str = scenario.WIDGET_PROMPT) -> types.CallToolResult:
    """Generate an interactive widget (HTML) for a request the standard components cannot express."""
    html = strip_fences(llm.text(system=SYSTEM, user=request, fixture="break_even"))
    problems = check_html(html)
    if problems:
        return types.CallToolResult(content=[types.TextContent(type="text", text="Widget rejected: " + "; ".join(problems))], is_error=True)
    return result(f"Generated an interactive widget ({tokens.count(html)} tokens of HTML) for: {request}",
                  {"title": "Break-even calculator", "html": html, "allowedEvents": ["apply_price"]})


@server.resource(VIEW_URI, name="widget_host_view", mime_type=MIME, meta=VIEW_META)
def widget_view() -> str:
    return build_view(HERE / "view.html")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--stdio", action="store_true", help="speak MCP over stdin/stdout (default)")
    cli.parse_args()
    server.run(transport="stdio")
