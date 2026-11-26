"""The coffee-cart dashboard as json-render specs (template, declarative, hybrid).

Used by lab 1 as the developer's template and by ``tools/make_fixtures.py``
to author the scripted model replies of labs 2-4.
"""

from __future__ import annotations

import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import scenario as s  # noqa: E402
from common.specs import break_even_html  # noqa: E402


def E(kind, props=None, children=None, **extra):
    return {"type": kind, "props": props or {}, "children": children or [], **extra}


def state_data() -> dict:
    k, t = s.kpis(), s.items_table()
    return {
        "kpis": {"revenue": s.money(k["revenue"]), "revenue_delta": k["revenue_delta"], "cups": f"{k['cups']:,}",
                 "cups_delta": k["cups_delta"], "ticket": s.money(k["avg_ticket"])},
        "week": {"labels": s.week_labels(), "values": s.week_revenue()},
        "items": {"columns": t["columns"], "rows": t["rows"]},
        "inventory": {"beans_kg": s.INVENTORY["beans_kg"], "label": f"Beans on hand: {s.INVENTORY['beans_kg']} kg (reorder at {s.INVENTORY['reorder_point_kg']} kg)."},
        "ui": {"showItems": True},
    }


def template_spec() -> dict:
    """Static mode: every value is a $state expression; the agent supplies only the state."""
    st = lambda p: {"$state": p}  # noqa: E731
    return {"root": "dash", "elements": {
        "dash": E("Card", {"title": f"{s.CART_NAME} - this week", "subtitle": "json-render template + agent state"},
                  ["kpis", "chart", "toggle", "items", "stock"]),
        "kpis": E("Row", {}, ["m-rev", "m-cups", "m-ticket"]),
        "m-rev": E("Metric", {"label": "Revenue", "value": st("/kpis/revenue"), "delta": st("/kpis/revenue_delta")}),
        "m-cups": E("Metric", {"label": "Cups sold", "value": st("/kpis/cups"), "delta": st("/kpis/cups_delta")}),
        "m-ticket": E("Metric", {"label": "Avg ticket", "value": st("/kpis/ticket"), "delta": None}),
        "chart": E("BarChart", {"title": "Revenue by day (USD)", "labels": st("/week/labels"), "values": st("/week/values")}),
        "toggle": E("Button", {"label": {"$cond": {"$state": "/ui/showItems"}, "$then": "Hide top items", "$else": "Show top items"}},
                    on={"press": {"action": "setState", "params": {"statePath": "/ui/showItems",
                                                                   "value": {"$cond": {"$state": "/ui/showItems"}, "$then": False, "$else": True}}}}),
        "items": E("Table", {"columns": st("/items/columns"), "rows": st("/items/rows")}, visible={"$state": "/ui/showItems"}),
        "stock": E("Row", {}, ["beans", "restock"]),
        "beans": E("Text", {"text": st("/inventory/label"), "tone": "strong"}),
        "restock": E("Button", {"label": "Reorder 10 kg of beans"}, on={"press": {"action": "restock_beans", "params": {"kg": 10}}}),
    }}


def dashboard_spec(hybrid: bool = False) -> dict:
    """Declarative mode: the model writes concrete props (and, in the hybrid, one HtmlBlock)."""
    k, t, d = s.kpis(), s.items_table(), state_data()
    elements = {
        "dash": E("Card", {"title": f"{s.CART_NAME} - this week", "subtitle": "Mon-Sun, all locations"}, ["kpis", "chart", "items", "stock"]),
        "kpis": E("Row", {}, ["m-rev", "m-cups", "m-ticket"]),
        "m-rev": E("Metric", {"label": "Revenue", "value": s.money(k["revenue"]), "delta": k["revenue_delta"]}),
        "m-cups": E("Metric", {"label": "Cups sold", "value": f"{k['cups']:,}", "delta": k["cups_delta"]}),
        "m-ticket": E("Metric", {"label": "Avg ticket", "value": s.money(k["avg_ticket"]), "delta": None}),
        "chart": E("BarChart", {"title": "Revenue by day (USD)", "labels": s.week_labels(), "values": s.week_revenue()}),
        "items": E("Table", {"columns": t["columns"], "rows": t["rows"]}),
        "stock": E("Row", {}, ["beans", "restock"]),
        "beans": E("Text", {"text": d["inventory"]["label"], "tone": "strong"}),
        "restock": E("Button", {"label": "Reorder 10 kg of beans"}, on={"press": {"action": "restock_beans", "params": {"kg": 10}}}),
    }
    state = {}
    if hybrid:
        elements["dash"]["children"] = ["kpis", "whatif", "chart", "toggle", "items", "stock"]
        elements["m-ticket"]["props"]["value"] = {"$state": "/kpis/ticket"}
        elements["beans"]["props"]["text"] = {"$state": "/inventory/label"}
        elements["items"]["visible"] = {"$state": "/ui/showItems"}
        elements["toggle"] = E("Button", {"label": {"$cond": {"$state": "/ui/showItems"}, "$then": "Hide top items", "$else": "Show top items"}},
                               on={"press": {"action": "setState", "params": {"statePath": "/ui/showItems",
                                                                              "value": {"$cond": {"$state": "/ui/showItems"}, "$then": False, "$else": True}}}})
        elements["whatif"] = E("HtmlBlock", {"title": "What-if price calculator", "html": break_even_html(), "caption": {"$state": "/whatif/status"}},
                               on={"apply_price": {"action": "apply_price"}})
        state = {"kpis": {"ticket": s.money(k["avg_ticket"])}, "inventory": {"beans_kg": s.INVENTORY["beans_kg"], "label": d["inventory"]["label"]},
                 "ui": {"showItems": True}, "whatif": {"status": "Move the sliders, then press 'Use this price'."}}
    return {"root": "dash", "elements": elements, "state": state}


def html_spec() -> dict:
    """Open-ended mode: a single HtmlBlock is the whole UI."""
    return {"root": "widget", "elements": {
        "widget": E("HtmlBlock", {"title": "Break-even calculator", "html": break_even_html(), "caption": {"$state": "/status"}},
                    on={"apply_price": {"action": "apply_price"}}),
    }, "state": {"status": "Model-written widget. Waiting for a price."}}


def to_patches(spec: dict) -> list[dict]:
    """SpecStream order: /root, then each element parent-first, then state (one patch per key)."""
    ops = [{"op": "add", "path": "/root", "value": spec["root"]}]
    seen = []

    def walk(eid):
        if eid in seen or eid not in spec["elements"]:
            return
        seen.append(eid)
        for c in spec["elements"][eid].get("children", []):
            walk(c)

    walk(spec["root"])
    seen += [e for e in spec["elements"] if e not in seen]
    ops += [{"op": "add", "path": f"/elements/{e}", "value": spec["elements"][e]} for e in seen]
    ops += [{"op": "add", "path": f"/state/{k}", "value": v} for k, v in (spec.get("state") or {}).items()]
    return ops
