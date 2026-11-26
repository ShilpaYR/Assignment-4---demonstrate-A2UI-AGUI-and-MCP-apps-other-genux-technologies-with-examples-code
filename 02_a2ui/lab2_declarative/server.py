"""Part 2 / Lab 2 - A2UI, DECLARATIVE mode: the model writes the surface.

Now the model writes the A2UI messages itself - createSurface,
updateComponents (a flat list from the Basic Catalog) and updateDataModel -
as JSONL, one message per line. The prompt is generated from the official
basic catalog. Every message is validated against the official A2UI v1.0
JSON Schemas *before* it is streamed.

Validation errors are not a dead end; they are feedback. If the reply does
not validate, the errors go back to the model and it tries again (at most
three attempts). The scripted first attempt makes two mistakes a model
trained on older A2UI really makes: a ``"variant": "h2"`` heading (removed
in v1.0) and a ``{"path": ...}`` binding (v1.0 requires ``"@path"``).

The surface is streamed in batches (root first), so the renderer shows
placeholders for children that have not arrived yet. The form uses two-way
binding: what the user types lives in the data model until a Button's
action carries it to the agent.

    python server.py            # http://127.0.0.1:8022
"""

from __future__ import annotations

import argparse
import json
import sys
import time
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

import a2ui  # noqa: E402
from common import scenario  # noqa: E402
from common.llm import get_llm, stream_delay  # noqa: E402
from common.web import SSE, App, Response, sse_frame  # noqa: E402

PORT = 8022
MAX_ATTEMPTS = 3
SYSTEM = a2ui.catalog_prompt() + (
    "\nBuild a dashboard (KPIs as Cards, top items as a List template over /items, beans on hand with a "
    "restock_beans Button) and a bean order form (TextField kg bound to /order/kg, TextField note, CheckBox "
    "express, Button submit_order whose context carries the three bound values)."
    f"\nData:\n{scenario.as_text()}"
)

llm = get_llm(HERE / "fixtures")


def generate(prompt: str):
    """Yield ("attempt", info) events and finally ("messages", list). The correction loop."""
    user = prompt
    for attempt in range(1, MAX_ATTEMPTS + 1):
        reply = llm.text(system=SYSTEM, user=user, fixture=f"attempt{attempt}")
        try:
            messages = a2ui.parse_jsonl(reply)
            errors = a2ui.validate_stream(messages)
        except json.JSONDecodeError as exc:
            messages, errors = [], [f"line is not JSON: {exc}"]
        yield "attempt", {"attempt": attempt, "valid": not errors, "errors": errors}
        if not errors:
            yield "messages", messages
            return
        # validation errors are a result: send them back and ask for a corrected stream
        user = (f"{prompt}\n\nYour previous A2UI messages failed validation:\n- " + "\n- ".join(errors)
                + "\nReturn the complete corrected JSONL.")
    raise RuntimeError(f"no valid A2UI after {MAX_ATTEMPTS} attempts")


def batches(messages: list[dict]):
    """Stream updateComponents in three parts, root first, so placeholders are visible."""
    for m in messages:
        if "updateComponents" in m:
            comps, sid = m["updateComponents"]["components"], m["updateComponents"]["surfaceId"]
            third = max(1, len(comps) // 3)
            for i in range(0, len(comps), third):
                yield a2ui.update_components(sid, comps[i:i + third])
        else:
            yield m


def frames(prompt: str):
    for kind, value in generate(prompt):
        if kind == "attempt":
            yield sse_frame(value, event="genux")       # meta event: not an A2UI message
        else:
            for m in batches(value):
                if stream_delay():
                    time.sleep(stream_delay() * 60)
                yield sse_frame(m)


def handle_action(msg: dict) -> list[dict]:
    errors = a2ui.validate_action(msg)
    if errors:
        return [{"error": errors}]
    act, sid = msg["action"], msg["action"]["surfaceId"]
    ctx = act["context"]
    if act["name"] == "submit_order":
        kg = ctx.get("kg")
        if not isinstance(kg, (int, float)) or not 1 <= kg <= 50:
            return [a2ui.update_data_model(sid, "/order/status", "Please enter between 1 and 50 kg.")]
        extra = (" express" if ctx.get("express") else "") + (f", note: {ctx['note']}" if ctx.get("note") else "")
        return [a2ui.update_data_model(sid, "/order/status", f"Order #1042 confirmed: {kg:g} kg{extra}.")]
    if act["name"] == "restock_beans":
        return [a2ui.update_data_model(sid, "/inventory/beans_kg", float(ctx["beansNow"]) + float(ctx["kg"])),
                a2ui.update_data_model(sid, "/inventory/status", f"Ordered {ctx['kg']} kg.")]
    return [{"error": [f"unknown action {act['name']!r}"]}]


def build_app() -> App:
    app = App(HERE / "page", title="A2UI lab 2 (declarative)")
    app.mount("a2ui", SHARED / "web")

    @app.post("/a2ui/stream")
    def a2ui_stream(req):
        return SSE(frames((req.json() or {}).get("prompt") or scenario.DASHBOARD_PROMPT))

    @app.post("/a2ui/action")
    def a2ui_action(req):
        out = handle_action(req.json())
        return Response(json.dumps(out), 400 if "error" in out[0] else 200, "application/json")

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
