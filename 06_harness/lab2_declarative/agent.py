"""Part 6 / Lab 2 - Harness integration, DECLARATIVE mode: a validated render_ui tool.

The harness gets one UI tool, ``render_ui(spec)``, whose argument is a flat
element map from the course catalog. The tool **validates** the spec; an
invalid spec is returned to the model as an ordinary tool error, and the
agent loop does the rest: the model reads the error and calls ``render_ui``
again with a fixed spec. Self-correction needs no extra machinery - it is
just the loop.

The scripted session's first attempt uses a ``PieChart`` (not in the
catalog) and a chart with 7 labels but 5 values.

    python agent.py              # terminal surface
    python agent.py --web        # web surface on http://127.0.0.1:8062
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from common import scenario  # noqa: E402
from common.catalog import catalog_prompt, validate_spec  # noqa: E402
from common.llm import get_llm  # noqa: E402
from harness import Harness, Tool, Workspace  # noqa: E402

PORT = 8062
ACTIONS = {"restock_beans": "order beans (params: kg)"}
SYSTEM = ("You are a coding agent with a data workspace. Read the files you need, then call render_ui ONCE with a "
          "dashboard built from this catalog. If render_ui returns errors, fix them and call it again.\n"
          + catalog_prompt(actions=ACTIONS).split("\n", 1)[1])


def render_ui(spec: dict) -> dict:
    """The UI tool: validate first; the error text is written for the model to act on."""
    errors = validate_spec(spec, actions=set(ACTIONS))
    if errors:
        return {"error": "render_ui rejected the spec: " + "; ".join(errors)}
    return {"spec": spec, "shown": True}


RENDER_UI = Tool("render_ui", "Render a UI from the component catalog. Argument: a flat element map {root, elements}.",
                 {"type": "object", "properties": {"spec": {"type": "object"}}, "required": ["spec"]}, render_ui, ui=True)


def build_harness() -> Harness:
    return Harness(llm=get_llm(HERE / "fixtures"), system=SYSTEM, tools=Workspace().tools() + [RENDER_UI], fixture="session")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--web", action="store_true")
    cli.add_argument("--port", type=int, default=PORT)
    args = cli.parse_args()
    harness = build_harness()
    if args.web:
        from web import build_web
        build_web(harness, title="Lab 2 - render_ui with self-correction", mode="declarative", prompt=scenario.DASHBOARD_PROMPT).serve(args.port)
    else:
        from surfaces import TerminalSurface
        term = TerminalSurface()
        harness.on(term).run(scenario.DASHBOARD_PROMPT)
        print(term.text())
