"""Part 2 / Lab 1 - A2UI, STATIC mode.

In A2UI, structure (components) and data (the data model) are separate
streams. Static mode uses that split directly:

* the **developer** writes the surface once - a flat list of Basic Catalog
  components whose values are bindings such as ``{"@path": "/kpis/revenue"}``;
* the **agent** never touches structure. It fills one function call,
  ``fill_dashboard(kpis, items, inventory)``, and the server turns the
  arguments into ``updateDataModel`` messages.

Wire (SSE, one A2UI message per event):
    createSurface   (components inline - the developer's template)
    updateDataModel /kpis, /items, /inventory   (from the agent)

A Button click comes back as an A2UI ``action`` message (POST /a2ui/action);
the agent answers with more ``updateDataModel`` messages.

    python server.py            # http://127.0.0.1:8021
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

from jsonschema import Draft202012Validator  # noqa: E402

import a2ui  # noqa: E402
from common import scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.web import SSE, App, Response, sse_frame  # noqa: E402
from dashboard import dashboard_components  # noqa: E402

PORT = 8021
SURFACE = "coffee_dashboard"

# The developer's template: written once, bound to data paths, never generated.
TEMPLATE = dashboard_components()

# The only thing the model may produce: the data the template binds to.
FILL_TOOL = {
    "name": "fill_dashboard",
    "description": "Fill the coffee-cart dashboard with this week's numbers.",
    "parameters": {
        "type": "object", "required": ["kpis", "items", "inventory"], "additionalProperties": False,
        "properties": {
            "kpis": {"type": "object", "required": ["revenue", "cups", "ticket"],
                     "properties": {k: {"type": "string"} for k in ("revenue", "cups", "ticket")}},
            "items": {"type": "array", "items": {"type": "object", "required": ["name", "cups", "revenue"],
                      "properties": {"name": {"type": "string"}, "cups": {"type": "integer"}, "revenue": {"type": "string"}}}},
            "inventory": {"type": "object", "required": ["beans_kg", "reorder_kg"],
                          "properties": {"beans_kg": {"type": "number"}, "reorder_kg": {"type": "number"}, "status": {"type": "string"}}},
        },
    },
}
SYSTEM = f"You fill a fixed dashboard. Call fill_dashboard exactly once.\nData:\n{scenario.as_text()}"

llm = get_llm(HERE / "fixtures")


def stream(prompt: str):
    """Structure first (developer), then data (agent)."""
    msgs = [a2ui.create_surface(SURFACE, a2ui.BASIC_CATALOG_ID, components=TEMPLATE)]
    reply = llm.chat(messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": prompt}],
                     tools=[FILL_TOOL], fixture="fill_dashboard")
    call = next(c for c in reply["tool_calls"] if c["name"] == "fill_dashboard")
    errors = [e.message for e in Draft202012Validator(FILL_TOOL["parameters"]).iter_errors(call["arguments"])]
    if errors:
        raise ValueError("fill_dashboard arguments invalid: " + "; ".join(errors))
    for key in ("kpis", "items", "inventory"):
        msgs.append(a2ui.update_data_model(SURFACE, f"/{key}", call["arguments"][key]))
    for m in msgs:
        assert not a2ui.validate_message(m), a2ui.validate_message(m)  # never send what a renderer would reject
    return msgs


def handle_action(msg: dict) -> list[dict]:
    """renderer -> agent: validate the action, answer with data-model updates."""
    errors = a2ui.validate_action(msg)
    if errors:
        return [{"error": errors}]
    act = msg["action"]
    if act["name"] == "restock_beans":
        kg, beans = float(act["context"]["kg"]), float(act["context"]["beansNow"])
        return [a2ui.update_data_model(act["surfaceId"], "/inventory/beans_kg", beans + kg),
                a2ui.update_data_model(act["surfaceId"], "/inventory/status", f"Ordered {kg:g} kg at {act['timestamp'][11:16]} UTC.")]
    return [a2ui.update_data_model(act["surfaceId"], "/inventory/status", f"Unknown action {act['name']!r} ignored.")]


def build_app() -> App:
    app = App(HERE / "page", title="A2UI lab 1 (static)")
    app.mount("a2ui", SHARED / "web")

    @app.post("/a2ui/stream")
    def a2ui_stream(req):
        prompt = (req.json() or {}).get("prompt") or scenario.DASHBOARD_PROMPT
        return SSE(sse_frame(m) for m in stream(prompt))

    @app.post("/a2ui/action")
    def a2ui_action(req):
        out = handle_action(req.json())
        return Response(__import__("json").dumps(out), 400 if "error" in out[0] else 200, "application/json")

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
