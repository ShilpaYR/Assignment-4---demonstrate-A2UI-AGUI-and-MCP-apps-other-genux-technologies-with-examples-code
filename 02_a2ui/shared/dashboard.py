"""The coffee-cart dashboard as A2UI v1.0 components and data.

Lab 1 uses ``dashboard_components()`` as its developer-written template
(static mode). ``tools/make_fixtures.py`` uses the same builders to author
the scripted model replies of labs 2 and 4, so every A2UI lab draws the
same dashboard.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import scenario as s  # noqa: E402

from a2ui import HTML_CATALOG_ID  # noqa: E402


def fmt(template: str) -> dict:
    """A2UI basic-catalog function call: formatString("... ${/path} ...")."""
    return {"@call": "formatString", "args": {"value": template}}


def kpi(cid: str, label: str, path: str) -> list[dict]:
    return [
        {"id": cid, "component": "Card", "child": f"{cid}_col"},
        {"id": f"{cid}_col", "component": "Column", "children": [f"{cid}_label", f"{cid}_value"]},
        {"id": f"{cid}_label", "component": "Text", "text": label, "variant": "caption"},
        {"id": f"{cid}_value", "component": "Text", "text": fmt("### ${" + path + "}")},
    ]


def dashboard_components(order_form: bool = False, html: str | None = None, close_button: bool = False) -> list[dict]:
    children = ["title", "kpis", "items_card", "stock_card"]
    comps = [
        {"id": "root", "component": "Column", "children": children},
        {"id": "title", "component": "Text", "text": f"## {s.CART_NAME} - this week"},
        {"id": "kpis", "component": "Row", "children": ["k_rev", "k_cups", "k_ticket"]},
        *kpi("k_rev", "Revenue", "/kpis/revenue"),
        *kpi("k_cups", "Cups sold", "/kpis/cups"),
        *kpi("k_ticket", "Avg ticket", "/kpis/ticket"),
        {"id": "items_card", "component": "Card", "child": "items_col"},
        {"id": "items_col", "component": "Column", "children": ["items_title", "items_list"]},
        {"id": "items_title", "component": "Text", "text": "#### Top items"},
        # a List TEMPLATE: one item_row per entry of /items, with paths relative to that entry
        {"id": "items_list", "component": "List", "children": {"componentId": "item_row", "path": "/items"}},
        {"id": "item_row", "component": "Row", "children": ["item_name", "item_cups", "item_rev"]},
        {"id": "item_name", "component": "Text", "text": {"@path": "name"}},
        {"id": "item_cups", "component": "Text", "text": fmt("${cups} cups"), "variant": "caption"},
        {"id": "item_rev", "component": "Text", "text": {"@path": "revenue"}},
        {"id": "stock_card", "component": "Card", "child": "stock_col"},
        {"id": "stock_col", "component": "Column", "children": ["stock_text", "restock_btn", "stock_status"]},
        {"id": "stock_text", "component": "Text",
         "text": fmt("Beans on hand: **${/inventory/beans_kg} kg** (reorder at ${/inventory/reorder_kg} kg)")},
        {"id": "restock_label", "component": "Text", "text": "Reorder 10 kg of beans"},
        {"id": "restock_btn", "component": "Button", "child": "restock_label", "variant": "primary",
         "action": {"event": {"name": "restock_beans", "context": {"kg": 10, "beansNow": {"@path": "/inventory/beans_kg"}}}}},
        {"id": "stock_status", "component": "Text", "text": {"@path": "/inventory/status"}, "variant": "caption"},
    ]
    if order_form:
        children.append("order_card")
        comps += [
            {"id": "order_card", "component": "Card", "child": "order_col"},
            {"id": "order_col", "component": "Column", "children": ["order_title", "order_kg", "order_note", "order_express", "order_btn", "order_status"]},
            {"id": "order_title", "component": "Text", "text": "#### Custom bean order"},
            {"id": "order_kg", "component": "TextField", "label": "Kilograms", "value": {"@path": "/order/kg"}, "variant": "number"},
            {"id": "order_note", "component": "TextField", "label": "Note for the roaster", "value": {"@path": "/order/note"}, "placeholder": "e.g. medium roast"},
            {"id": "order_express", "component": "CheckBox", "label": "Express delivery", "value": {"@path": "/order/express"}},
            {"id": "order_btn_label", "component": "Text", "text": "Place order"},
            {"id": "order_btn", "component": "Button", "child": "order_btn_label",
             "action": {"event": {"name": "submit_order", "context": {
                 "kg": {"@path": "/order/kg"}, "note": {"@path": "/order/note"}, "express": {"@path": "/order/express"}}}}},
            {"id": "order_status", "component": "Text", "text": {"@path": "/order/status"}, "variant": "caption"},
        ]
    if html is not None:
        children.insert(2, "whatif")
        comps.append({"id": "whatif", "component": "HtmlFrame", "@catalogId": HTML_CATALOG_ID,
                      "title": "What-if price calculator", "html": html, "caption": {"@path": "/whatif/status"},
                      "allowedEvents": ["apply_price"]})
    if close_button:
        children.append("close_btn")
        comps += [{"id": "close_label", "component": "Text", "text": "Close dashboard"},
                  {"id": "close_btn", "component": "Button", "child": "close_label", "variant": "borderless",
                   "action": {"event": {"name": "close_surface", "context": {}}}}]
    return comps


def dashboard_data() -> dict:
    k = s.kpis()
    return {
        "kpis": {"revenue": s.money(k["revenue"]), "cups": f"{k['cups']:,}", "ticket": s.money(k["avg_ticket"])},
        "items": [{"name": n, "cups": c, "revenue": s.money(r)} for n, c, r in s.TOP_ITEMS],
        "inventory": {"beans_kg": s.INVENTORY["beans_kg"], "reorder_kg": s.INVENTORY["reorder_point_kg"], "status": ""},
    }
