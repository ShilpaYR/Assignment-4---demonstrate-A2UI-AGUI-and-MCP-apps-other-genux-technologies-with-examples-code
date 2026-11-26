"""Author the scripted model replies (``fixtures/``) for every lab.

Each lab's ScriptedLLM replays a file from its ``fixtures/`` folder. This
script writes those files from the canonical content in ``common/specs.py``
so that all 24 labs show the *same* dashboard and the *same* generated
calculator, each in its own format. The output files are committed; run
this script again only if you change the scenario.

    python tools/make_fixtures.py
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))

from common import scenario as s  # noqa: E402
from common.specs import break_even_html, dashboard_spec  # noqa: E402

WRITERS = []


def writer(fn):
    WRITERS.append(fn)
    return fn


def put(rel: str, content):
    path = ROOT / rel
    path.parent.mkdir(parents=True, exist_ok=True)
    if not isinstance(content, str):
        content = json.dumps(content, indent=2) + "\n"
    path.write_text(content, encoding="utf-8")
    print("wrote", rel)


def static_tool_calls() -> list[dict]:
    k, t = s.kpis(), s.items_table()
    return [
        {"name": "show_metric", "arguments": {"label": "Revenue", "value": s.money(k["revenue"]), "delta": k["revenue_delta"]}},
        {"name": "show_metric", "arguments": {"label": "Cups sold", "value": f"{k['cups']:,}", "delta": k["cups_delta"]}},
        {"name": "show_metric", "arguments": {"label": "Avg ticket", "value": s.money(k["avg_ticket"])}},
        {"name": "show_chart", "arguments": {"title": "Revenue by day (USD)", "labels": s.week_labels(), "values": s.week_revenue()}},
        {"name": "show_table", "arguments": {"columns": t["columns"], "rows": t["rows"]}},
    ]


# ------------------------------------------------------------------ Part 1: AG-UI
@writer
def ag_ui():
    put("01_ag_ui/lab1_static/fixtures/dashboard.json", [
        {"content": f"Revenue is up {s.kpis()['revenue_delta']} this week; Friday was the best day.",
         "tool_calls": static_tool_calls()},
    ])
    put("01_ag_ui/lab2_declarative/fixtures/dashboard_spec.json", dashboard_spec(with_action=False))
    put("01_ag_ui/lab3_open_ended/fixtures/break_even.html", break_even_html())
    put("01_ag_ui/lab4_mixed/fixtures/dashboard_hybrid.json", dashboard_spec(hybrid=True))


# ------------------------------------------------------------------ Part 2: A2UI
def _jsonl(msgs) -> str:
    return "\n".join(json.dumps(m, separators=(",", ":")) for m in msgs) + "\n"


@writer
def a2ui():
    sys.path.insert(0, str(ROOT / "02_a2ui" / "shared"))
    import a2ui as A
    from dashboard import dashboard_components, dashboard_data

    data = dashboard_data()
    put("02_a2ui/lab1_static/fixtures/fill_dashboard.json", [{"content": None, "tool_calls": [
        {"name": "fill_dashboard", "arguments": data}]}])

    good = dashboard_components(order_form=True)
    data2 = {**data, "order": {"kg": 12, "note": "", "express": False, "status": ""}}
    # attempt 1: two mistakes a model trained on older A2UI versions really makes
    bad = json.loads(json.dumps(good))
    for c in bad:
        if c["id"] == "title":
            c["text"], c["variant"] = f"{s.CART_NAME} - this week", "h2"      # v0.9 heading variant
        if c["id"] == "item_name":
            c["text"] = {"path": "name"}                                        # v0.9 binding without '@'
    surface = "coffee_dashboard"
    put("02_a2ui/lab2_declarative/fixtures/attempt1.jsonl", _jsonl([
        A.create_surface(surface), A.update_components(surface, bad), A.update_data_model(surface, "/", data2)]))
    put("02_a2ui/lab2_declarative/fixtures/attempt2.jsonl", _jsonl([
        A.create_surface(surface), A.update_components(surface, good), A.update_data_model(surface, "/", data2)]))

    put("02_a2ui/lab3_open_ended/fixtures/break_even.html", break_even_html())

    mixed = dashboard_components(html=break_even_html(), close_button=True)
    data4 = {**data, "whatif": {"status": "Pick a price and press 'Use this price'."}}
    put("02_a2ui/lab4_mixed/fixtures/dashboard_mixed.jsonl", _jsonl([
        A.create_surface(surface), A.update_components(surface, mixed), A.update_data_model(surface, "/", data4)]))


# ------------------------------------------------------------------ Part 3: json-render
@writer
def json_render():
    sys.path.insert(0, str(ROOT / "03_json_render" / "shared"))
    import specs as J

    data = J.state_data()
    data.pop("ui")
    put("03_json_render/lab1_static/fixtures/fill_state.json", [{"content": None, "tool_calls": [
        {"name": "fill_state", "arguments": data}]}])

    ops = J.to_patches(J.dashboard_spec())  # the declarative spec has no state: elements only
    # a hallucinated component, streamed mid-way: the server must drop this one line
    ops.insert(6, {"op": "add", "path": "/elements/pie", "value": {"type": "PieChart", "props": {"slices": [1, 2]}, "children": []}})
    put("03_json_render/lab2_declarative/fixtures/dashboard.jsonl", _jsonl(ops))
    put("03_json_render/lab3_open_ended/fixtures/widget.jsonl", _jsonl(J.to_patches(J.html_spec())))
    put("03_json_render/lab4_mixed/fixtures/dashboard_hybrid.jsonl", _jsonl(J.to_patches(J.dashboard_spec(hybrid=True))))


# ------------------------------------------------------------------ Part 4: OpenUI Lang
@writer
def openui():
    sys.path.insert(0, str(ROOT / "04_openui" / "shared"))
    import programs as P

    put("04_openui/lab1_static/fixtures/dashboard.oui", P.static_program())
    put("04_openui/lab2_declarative/fixtures/dashboard.oui", P.declarative_program())
    put("04_openui/lab3_open_ended/fixtures/calculator.oui", P.html_program())
    put("04_openui/lab4_mixed/fixtures/dashboard_hybrid.oui", P.hybrid_program())


# ------------------------------------------------------------------ Part 5: MCP Apps
@writer
def mcp_apps():
    put("05_mcp_apps/lab2_declarative/fixtures/dashboard_spec.json", dashboard_spec())
    put("05_mcp_apps/lab3_open_ended/fixtures/break_even.html", break_even_html())
    put("05_mcp_apps/lab4_mixed/fixtures/dashboard_hybrid.json", dashboard_spec(hybrid=True))


# ------------------------------------------------------------------ Part 6: harness integration
def _reads(*files):
    return [{"name": "read_file", "arguments": {"path": f}} for f in files]


@writer
def harness():
    from common.specs import dashboard_spec as flat_spec

    put("06_harness/lab1_static/fixtures/session.json", [
        {"content": "I'll look at the workspace first.", "tool_calls": [{"name": "list_files", "arguments": {}}]},
        {"content": None, "tool_calls": _reads("sales_week.csv", "top_items.csv")},
        {"content": None, "tool_calls": static_tool_calls()},
        {"content": f"Revenue was {s.money(s.kpis()['revenue'])} this week; Friday was the best day.", "tool_calls": []},
    ])

    good = flat_spec()
    bad = json.loads(json.dumps(good))
    bad["elements"]["chart"]["props"]["values"] = bad["elements"]["chart"]["props"]["values"][:5]   # 7 labels, 5 values
    bad["elements"]["pie"] = {"type": "PieChart", "props": {"slices": [1, 2]}, "children": []}
    bad["elements"]["dash"]["children"].append("pie")
    put("06_harness/lab2_declarative/fixtures/session.json", [
        {"content": None, "tool_calls": _reads("sales_week.csv", "top_items.csv", "inventory.json")},
        {"content": None, "tool_calls": [{"name": "render_ui", "arguments": {"spec": bad}}]},
        {"content": "The catalog has no PieChart and the chart needs 7 values; fixing the layout.",
         "tool_calls": [{"name": "render_ui", "arguments": {"spec": good}}]},
        {"content": "Dashboard rendered from the catalog after one correction.", "tool_calls": []},
    ])

    put("06_harness/lab3_open_ended/fixtures/session.json", [
        {"content": None, "tool_calls": _reads("sales_week.csv")},
        {"content": "No catalog component can do this, so I'll write a small HTML calculator.",
         "tool_calls": [{"name": "render_html", "arguments": {"title": "Break-even calculator", "html": break_even_html()}}]},
        {"content": "The calculator is open in the web surface and saved as an artifact.", "tool_calls": []},
    ])

    hybrid = flat_spec(hybrid=True)
    put("06_harness/lab4_mixed/fixtures/session.json", [
        # run 1: the request
        {"content": None, "tool_calls": _reads("sales_week.csv", "top_items.csv", "inventory.json")},
        {"content": None, "tool_calls": [{"name": "render_ui", "arguments": {"spec": hybrid}}]},
        {"content": "Here is the week. The purple calculator is generated; everything else is from the catalog.", "tool_calls": []},
        # run 2: "[ui action] restock_beans {kg: 10}"
        {"content": None, "tool_calls": [{"name": "place_order", "arguments": {"kg": 10}}]},
        {"content": None, "tool_calls": [{"name": "update_ui", "arguments": {"ops": [
            {"op": "replace", "path": "/elements/note/props/text", "value": "Beans on hand: 13.5 kg - order #1 placed (written to inventory.json)."},
            {"op": "replace", "path": "/elements/restock/props/label", "value": "Reorder again"}]}}]},
        {"content": "Ordered 10 kg; inventory.json now shows 13.5 kg.", "tool_calls": []},
        # run 3: "[ui action] apply_price {price: ...}"
        {"content": None, "tool_calls": [{"name": "update_ui", "arguments": {"ops": [
            {"op": "replace", "path": "/elements/m-ticket/props/value", "value": "$4.20"},
            {"op": "add", "path": "/elements/m-ticket/props/delta", "value": "new list price"}]}}]},
        {"content": "Updated the average-ticket KPI to the price you picked in the calculator.", "tool_calls": []},
    ])


if __name__ == "__main__":
    only = set(sys.argv[1:])
    for w in WRITERS:
        if not only or w.__name__ in only:
            w()
