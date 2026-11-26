"""Part 6 / Lab 4 - Harness integration, MIXED mode: the whole loop, human in it.

Everything from labs 1-3 in one agent:

* workspace tools: ``read_file`` and ``place_order`` (which really edits
  ``inventory.json`` in the agent's workspace);
* UI tools: ``render_ui(spec)`` with the hybrid catalog (catalog components +
  one ``GeneratedView`` checked by the HTML policy) and ``update_ui(ops)``,
  which patches the rendered spec and re-validates it;
* the web surface bridges the run to AG-UI (text, tool calls, results,
  ``STATE_SNAPSHOT`` / ``STATE_DELTA``);
* a click in the UI - a catalog Button or an event from the sandboxed
  calculator - becomes the **next user turn** of the same conversation:
  ``[ui action] restock_beans {"kg": 10}``. The agent decides what to do with it.

    python agent.py --web        # http://127.0.0.1:8064
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from common import jsonpatch, scenario  # noqa: E402
from common.catalog import catalog_prompt, validate_spec  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from harness import Harness, Tool, Workspace  # noqa: E402

PORT = 8064
ACTIONS = {"restock_beans": "order beans (params: kg)"}
UI_EVENTS = {"restock_beans", "apply_price"}          # what the page may send back as a turn
SYSTEM = ("You are a coding agent for a coffee cart. Read the workspace, then call render_ui once. Messages that start with "
          "[ui action] come from the user's clicks: act on them with your tools, then call update_ui to show the result.\n"
          + catalog_prompt(hybrid=True, actions=ACTIONS).split("\n", 1)[1])


class UiState:
    """The spec currently on screen, owned by the agent's tools."""

    def __init__(self, workspace: Workspace):
        self.ws, self.spec = workspace, None

    def render_ui(self, spec: dict) -> dict:
        errors = validate_spec(spec, hybrid=True, actions=set(ACTIONS))
        views = [el for el in spec.get("elements", {}).values() if el.get("type") == "GeneratedView"]
        errors += ["use at most one GeneratedView"] if len(views) > 1 else []
        errors += [p for v in views for p in check_html(v["props"].get("html", ""))]
        if errors:
            return {"error": "render_ui rejected the spec: " + "; ".join(errors)}
        self.spec = spec
        return {"spec": spec, "shown": True}

    def update_ui(self, ops: list) -> dict:
        if self.spec is None:
            return {"error": "nothing rendered yet; call render_ui first"}
        new = jsonpatch.apply(self.spec, ops)
        errors = validate_spec(new, hybrid=True, actions=set(ACTIONS))
        if errors:
            return {"error": "update_ui would break the UI: " + "; ".join(errors)}
        self.spec = new
        return {"ops": ops}

    def place_order(self, kg: float) -> dict:
        kg = max(1.0, min(float(kg), 50.0))
        path = self.ws.path("inventory.json")
        inv = json.loads(path.read_text())
        inv["beans_kg"] = round(inv["beans_kg"] + kg, 1)
        inv["orders"].append({"id": len(inv["orders"]) + 1, "kg": kg})
        path.write_text(json.dumps(inv, indent=2))
        return {"order": inv["orders"][-1], "beans_kg": inv["beans_kg"]}


def build_harness() -> Harness:
    ws = Workspace()
    ui = UiState(ws)
    obj = {"type": "object"}
    tools = ws.tools() + [
        Tool("render_ui", "Render a hybrid UI {root, elements}.", {"type": "object", "properties": {"spec": obj}, "required": ["spec"]}, ui.render_ui, ui=True),
        Tool("update_ui", "Patch the UI on screen with RFC 6902 operations on the spec.",
             {"type": "object", "properties": {"ops": {"type": "array", "items": obj}}, "required": ["ops"]}, ui.update_ui, ui=True),
        Tool("place_order", "Order coffee beans; writes inventory.json.", {"type": "object", "properties": {"kg": {"type": "number"}}, "required": ["kg"]}, ui.place_order),
    ]
    h = Harness(llm=get_llm(HERE / "fixtures"), system=SYSTEM, tools=tools, fixture="session")
    h.workspace, h.ui_state = ws, ui
    return h


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    args = cli.parse_args()
    from web import build_web
    build_web(build_harness(), title="Lab 4 - the whole loop, human in it", mode="mixed", prompt=scenario.MIXED_PROMPT,
              actions=UI_EVENTS).serve(args.port)
