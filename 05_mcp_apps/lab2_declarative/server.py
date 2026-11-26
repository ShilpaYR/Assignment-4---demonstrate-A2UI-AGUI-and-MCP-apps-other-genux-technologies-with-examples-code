"""Part 5 / Lab 2 - MCP Apps, DECLARATIVE mode: the view is a catalog renderer.

The view no longer hard-codes a dashboard. It is a generic renderer for the
course's component catalog (flat element maps, see ``common/catalog.py``).
The tool ``render_dashboard(request)`` asks the server's own model for a
layout, validates it against the catalog, and returns it as
``structuredContent.spec``. The model key stays on the server; the host only
sees a validated spec.

User actions go through an app-only tool, ``ui_action(action, params)``,
whose result is a list of JSON Patch operations for the spec.

    python run_host.py           # http://127.0.0.1:8052
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from mcp import types  # noqa: E402
from mcp.server.mcpserver import MCPServer  # noqa: E402

from common import scenario  # noqa: E402
from common.catalog import catalog_prompt, parse_json_reply, validate_spec  # noqa: E402
from common.llm import get_llm  # noqa: E402
from mcpapps import MIME, VIEW_META, build_view, result, ui_meta  # noqa: E402

VIEW_URI = "ui://coffee/catalog-view.html"
ACTIONS = {"restock_beans": "order more beans (params: kg)"}
SYSTEM = catalog_prompt(actions=ACTIONS) + f"\n\nData:\n{scenario.as_text()}\nDaily revenue: {scenario.week_revenue()}"
server = MCPServer("coffee-cart-declarative")
llm = get_llm(HERE / "fixtures")


@server.tool(meta=ui_meta(VIEW_URI, ["model", "app"]))
def render_dashboard(request: str = scenario.DASHBOARD_PROMPT) -> types.CallToolResult:
    """Design and show a dashboard for the coffee cart from the component catalog."""
    spec = parse_json_reply(llm.text(system=SYSTEM, user=request, fixture="dashboard_spec"))
    errors = validate_spec(spec, actions=set(ACTIONS))
    if errors:  # isError results reach the model as text, so it can retry with another request
        return types.CallToolResult(content=[types.TextContent(type="text", text="Invalid layout: " + "; ".join(errors))], is_error=True)
    kinds = sorted({el["type"] for el in spec["elements"].values()})
    return result(f"Showing a {len(spec['elements'])}-element dashboard ({', '.join(kinds)}).", {"spec": spec})


@server.tool(meta=ui_meta(VIEW_URI, ["app"]))
def ui_action(action: str, params: dict | None = None) -> types.CallToolResult:
    """App-only: a Button in the view was pressed. Returns JSON Patch operations for the spec."""
    if action not in ACTIONS:
        return types.CallToolResult(content=[types.TextContent(type="text", text=f"unknown action {action}")], is_error=True)
    kg = float((params or {}).get("kg", 10))
    beans = scenario.INVENTORY["beans_kg"] + kg
    ops = [{"op": "replace", "path": "/elements/note/props/text", "value": f"Beans on hand: {beans:g} kg - {kg:g} kg ordered."}]
    return result(f"Ordered {kg:g} kg of beans.", {"ops": ops})


@server.resource(VIEW_URI, name="catalog_view", mime_type=MIME, meta=VIEW_META)
def catalog_view() -> str:
    return build_view(HERE / "view.html")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--stdio", action="store_true", help="speak MCP over stdin/stdout (default)")
    cli.parse_args()
    server.run(transport="stdio")
