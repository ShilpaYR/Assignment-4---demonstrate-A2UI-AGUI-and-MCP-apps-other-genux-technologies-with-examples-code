"""Part 3 / Lab 1 - json-render, STATIC mode: a template spec + agent state.

json-render specs have a ``state`` model, and any prop can read it with
``{"$state": "/kpis/revenue"}``. Static mode uses that:

* the **developer** writes the spec (elements, layout, bindings, one built-in
  ``setState`` toggle, one custom ``restock_beans`` action);
* the **agent** fills one function call, ``fill_state(...)``; the server sends
  its arguments as SpecStream patches on ``/state``.

Everything goes over SSE as RFC 6902 patches (json-render's SpecStream):

    {"op":"replace","path":"","value":{...template spec...}}     developer
    {"op":"add","path":"/state/kpis","value":{...}}             agent
    {"op":"add","path":"/state/week","value":{...}}             agent

    python server.py            # http://127.0.0.1:8031
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

from jsonschema import Draft202012Validator  # noqa: E402

import jr  # noqa: E402
from common import scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.web import SSE, App, sse_frame  # noqa: E402
from specs import template_spec  # noqa: E402

PORT = 8031
TEMPLATE = template_spec()          # written once by the developer
STRS = {"type": "string"}
FILL_TOOL = {
    "name": "fill_state",
    "description": "Provide the numbers the dashboard template displays.",
    "parameters": {"type": "object", "required": ["kpis", "week", "items", "inventory"], "properties": {
        "kpis": {"type": "object", "required": ["revenue", "cups", "ticket"], "properties": {
            k: STRS for k in ("revenue", "revenue_delta", "cups", "cups_delta", "ticket")}},
        "week": {"type": "object", "required": ["labels", "values"], "properties": {
            "labels": {"type": "array", "items": STRS}, "values": {"type": "array", "items": {"type": "number"}}}},
        "items": {"type": "object", "required": ["columns", "rows"], "properties": {
            "columns": {"type": "array", "items": STRS}, "rows": {"type": "array", "items": {"type": "array", "items": STRS}}}},
        "inventory": {"type": "object", "required": ["beans_kg", "label"], "properties": {"beans_kg": {"type": "number"}, "label": STRS}},
    }},
}
SYSTEM = f"Call fill_state once with this week's numbers.\n{scenario.as_text()}\nDaily revenue: {scenario.week_revenue()}"
llm = get_llm(HERE / "fixtures")


def patches(prompt: str) -> list[dict]:
    assert not jr.validate(TEMPLATE, "base"), jr.validate(TEMPLATE, "base")
    reply = llm.chat(messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                     tools=[FILL_TOOL], fixture="fill_state")
    args = next(c["arguments"] for c in reply["tool_calls"] if c["name"] == "fill_state")
    errors = [e.message for e in Draft202012Validator(FILL_TOOL["parameters"]).iter_errors(args)]
    if errors:
        raise ValueError("fill_state arguments invalid: " + "; ".join(errors))
    ops = [{"op": "replace", "path": "", "value": {**TEMPLATE, "state": {"ui": {"showItems": True}}}}]
    ops += [{"op": "add", "path": f"/state/{k}", "value": args[k]} for k in ("kpis", "week", "items", "inventory")]
    return ops


def handle_action(body: dict) -> list[dict]:
    """Custom actions come to the server; it answers with state patches."""
    if body.get("action") != "restock_beans":
        return [{"error": f"action {body.get('action')!r} is not in the catalog"}]
    kg = float(body.get("params", {}).get("kg", 0))
    beans = float(body.get("state", {}).get("inventory", {}).get("beans_kg", 0)) + kg
    return [{"op": "replace", "path": "/state/inventory/beans_kg", "value": beans},
            {"op": "replace", "path": "/state/inventory/label", "value": f"Beans on hand: {beans:g} kg - {kg:g} kg ordered."}]


def build_app() -> App:
    app = App(HERE / "page", title="json-render lab 1 (static)")
    app.mount("jr", SHARED / "web")

    @app.post("/jr/stream")
    def stream(req):
        return SSE(sse_frame(op) for op in patches((req.json() or {}).get("prompt") or scenario.DASHBOARD_PROMPT))

    @app.post("/jr/action")
    def action(req):
        return handle_action(req.json())

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
