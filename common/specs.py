"""Canonical content used to author the scripted model replies (fixtures).

``tools/make_fixtures.py`` turns these into each lab's ``fixtures/`` files
in that lab's own format (AG-UI tool calls, A2UI messages, json-render
patches, OpenUI Lang, ...). The fixtures are committed so a reader can
open them and see exactly what "the model" said.
"""

from __future__ import annotations

from pathlib import Path

from . import scenario as s

FIXTURES = Path(__file__).parent / "fixtures"


def break_even_html() -> str:
    return (FIXTURES / "break_even.html").read_text(encoding="utf-8")


def dashboard_spec(hybrid: bool = False, with_action: bool = True) -> dict:
    k = s.kpis()
    t = s.items_table()
    elements = {
        "dash": {"type": "Card", "props": {"title": f"{s.CART_NAME} - this week", "subtitle": "Mon-Sun, all locations"},
                 "children": ["kpis", "chart", "items"] + (["actions"] if with_action else [])},
        "kpis": {"type": "Row", "props": {}, "children": ["m-rev", "m-cups", "m-ticket"]},
        "m-rev": {"type": "Metric", "props": {"label": "Revenue", "value": s.money(k["revenue"]), "delta": k["revenue_delta"]}, "children": []},
        "m-cups": {"type": "Metric", "props": {"label": "Cups sold", "value": f"{k['cups']:,}", "delta": k["cups_delta"]}, "children": []},
        "m-ticket": {"type": "Metric", "props": {"label": "Avg ticket", "value": s.money(k["avg_ticket"])}, "children": []},
        "chart": {"type": "BarChart", "props": {"title": "Revenue by day (USD)", "labels": s.week_labels(), "values": s.week_revenue()}, "children": []},
        "items": {"type": "Table", "props": {"columns": t["columns"], "rows": t["rows"]}, "children": []},
    }
    if with_action:
        elements["actions"] = {"type": "Row", "props": {}, "children": ["note", "restock"]}
        elements["note"] = {"type": "Text", "props": {"text": f"Beans on hand: {s.INVENTORY['beans_kg']} kg (reorder at {s.INVENTORY['reorder_point_kg']} kg).", "tone": "strong"}, "children": []}
        elements["restock"] = {"type": "Button", "props": {"label": "Reorder 10 kg of beans", "action": "restock_beans", "params": {"kg": 10}}, "children": []}
    if hybrid:
        elements["dash"]["children"].insert(3, "whatif")
        elements["whatif"] = {"type": "GeneratedView", "props": {"title": "What-if price calculator", "html": break_even_html()}, "children": []}
    return {"root": "dash", "elements": elements}
