"""Part 5 / Lab 4 - MCP Apps, MIXED mode: catalog + a generated region, the key on the server.

``coffee_dashboard_hybrid(request)`` returns a hybrid spec: catalog components
plus one ``GeneratedView`` whose HTML the server's own model wrote. The view
renders the catalog itself and mounts the generated region in a nested
sandbox (host -> view -> generated iframe).

Interaction goes through **app-only tools** (``visibility: ["app"]``), so the
model cannot trigger them and the host enforces it:
* ``restock_beans(kg)``  - from the catalog Button;
* ``apply_price(price)`` - from the generated region (validated: untrusted input).
Both return JSON Patch operations for the spec. The view also updates the
model context so the conversation knows what the user did.

The tool's ``content`` is a complete text answer, so a host without UI
support (``shared/text_host.py``) still gives the user something useful.

    python run_host.py           # http://127.0.0.1:8054
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
from common.sandbox import check_html  # noqa: E402
from mcpapps import MIME, VIEW_META, build_view, result, ui_meta  # noqa: E402

VIEW_URI = "ui://coffee/hybrid-view.html"
ACTIONS = {"restock_beans": "order more beans (params: kg)"}
SYSTEM = catalog_prompt(hybrid=True, actions=ACTIONS) + f"\n\nData:\n{scenario.as_text()}"
server = MCPServer("coffee-cart-hybrid")
llm = get_llm(HERE / "fixtures")
STATE = {"beans_kg": scenario.INVENTORY["beans_kg"]}


def error(text: str) -> types.CallToolResult:
    return types.CallToolResult(content=[types.TextContent(type="text", text=text)], is_error=True)


@server.tool(meta=ui_meta(VIEW_URI, ["model", "app"]))
def coffee_dashboard_hybrid(request: str = scenario.MIXED_PROMPT) -> types.CallToolResult:
    """Dashboard for the coffee cart with an interactive what-if price calculator."""
    spec = parse_json_reply(llm.text(system=SYSTEM, user=request, fixture="dashboard_hybrid"))
    errors = validate_spec(spec, hybrid=True, actions=set(ACTIONS))
    views = [el for el in spec["elements"].values() if el["type"] == "GeneratedView"]
    errors += ["at most one GeneratedView"] if len(views) > 1 else []
    errors += [p for v in views for p in check_html(v["props"]["html"])]
    if errors:
        return error("Invalid layout: " + "; ".join(errors))
    return result(scenario.as_text() + "\n(Interactive what-if price calculator available in UI-capable hosts.)", {"spec": spec})


@server.tool(meta=ui_meta(VIEW_URI, ["app"]))
def restock_beans(kg: float = 10) -> types.CallToolResult:
    """App-only: order beans from the dashboard."""
    STATE["beans_kg"] = round(STATE["beans_kg"] + max(1.0, min(float(kg), 50.0)), 1)
    return result(f"Beans on hand {STATE['beans_kg']} kg.", {"ops": [
        {"op": "replace", "path": "/elements/note/props/text", "value": f"Beans on hand: {STATE['beans_kg']} kg - order placed."}]})


@server.tool(meta=ui_meta(VIEW_URI, ["app"]))
def apply_price(price: float) -> types.CallToolResult:
    """App-only: the generated calculator proposes a new list price. Untrusted input: validated."""
    if not 2 <= float(price) <= 7:
        return error(f"price {price} is outside 2-7 USD")
    return result(f"List price set to ${float(price):.2f}.", {"ops": [
        {"op": "replace", "path": "/elements/m-ticket/props/value", "value": f"${float(price):.2f}"},
        {"op": "add", "path": "/elements/m-ticket/props/delta", "value": "new list price"}]})


@server.resource(VIEW_URI, name="hybrid_view", mime_type=MIME, meta=VIEW_META)
def hybrid_view() -> str:
    return build_view(HERE / "view.html")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--stdio", action="store_true", help="speak MCP over stdin/stdout (default)")
    cli.parse_args()
    server.run(transport="stdio")
