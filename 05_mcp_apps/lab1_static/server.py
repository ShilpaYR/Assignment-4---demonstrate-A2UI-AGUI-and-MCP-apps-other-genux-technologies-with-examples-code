"""Part 5 / Lab 1 - MCP Apps, STATIC mode: a pre-built view for a tool result.

The MCP server exposes:
* ``coffee_dashboard(days)``  - visible to the model and the app; its
  ``_meta.ui.resourceUri`` points at the view; it returns ``content`` (text for
  the model / UI-less hosts) and ``structuredContent`` (data for the view);
* ``restock_beans(kg)``       - visible to the **app only** (``visibility: ["app"]``):
  the model cannot call it, the view can, through the host;
* the resource ``ui://coffee/dashboard.html`` - the view, a pre-built HTML
  document (static mode: the model chooses nothing about the UI).

    python server.py --stdio     # what hosts launch (Claude Desktop, Goose, our host.py)
    python run_host.py           # our browser host on http://127.0.0.1:8051
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
from mcpapps import MIME, VIEW_META, build_view, result, ui_meta  # noqa: E402

VIEW_URI = "ui://coffee/dashboard.html"
server = MCPServer("coffee-cart-static", instructions="Coffee-cart sales data with an interactive dashboard view.")
INVENTORY = scenario.inventory()


def dashboard_data(days: int) -> dict:
    days = max(1, min(int(days), 7))
    week = scenario.WEEK[-days:]
    kpis = scenario.kpis()
    if days < 7:  # KPIs for the selected window (no week-over-week delta for a partial week)
        cups, revenue = sum(c for _, c, _ in week), sum(r for _, _, r in week)
        kpis = {"revenue": round(revenue, 2), "cups": cups, "avg_ticket": round(revenue / cups, 2), "revenue_delta": None, "cups_delta": None}
    return {"days": days, "kpis": kpis, "labels": [d for d, _, _ in week], "revenue": [r for _, _, r in week],
            "items": scenario.items_table(), "inventory": dict(INVENTORY)}


@server.tool(meta=ui_meta(VIEW_URI, ["model", "app"]))
def coffee_dashboard(days: int = 7) -> types.CallToolResult:
    """Sales dashboard for the Campus Coffee Cart over the last `days` days (1-7)."""
    return result(scenario.as_text(), dashboard_data(days))


@server.tool(meta=ui_meta(VIEW_URI, ["app"]))
def restock_beans(kg: float = 10) -> types.CallToolResult:
    """Order coffee beans. App-only: called by the dashboard view, not by the model."""
    kg = max(1.0, min(float(kg), 50.0))
    INVENTORY["beans_kg"] = round(INVENTORY["beans_kg"] + kg, 1)
    return result(f"Ordered {kg:g} kg; beans on hand {INVENTORY['beans_kg']} kg.", {"inventory": dict(INVENTORY), "ordered_kg": kg})


@server.resource(VIEW_URI, name="coffee_dashboard_view", mime_type=MIME, meta=VIEW_META)
def dashboard_view() -> str:
    """The pre-built view. The data arrives later, over the bridge."""
    return build_view(HERE / "view.html")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--stdio", action="store_true", help="speak MCP over stdin/stdout (default)")
    cli.parse_args()
    server.run(transport="stdio")
