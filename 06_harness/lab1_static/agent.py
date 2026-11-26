"""Part 6 / Lab 1 - Harness integration, STATIC mode: UI tools next to file tools.

A coding-agent harness (the loop in ``shared/harness.py``) gets three
pre-built UI tools - ``show_metric``, ``show_chart``, ``show_table`` - next to
its ordinary workspace tools (``list_files``, ``read_file``). The agent reads
the CSV exports in its workspace, computes the numbers, and *calls UI tools*
to show them. The same run is drawn by two surfaces:

* the terminal (``python agent.py``): UI tool calls become ``rich`` panels;
* the browser (``python agent.py --web``): the run is bridged to AG-UI events
  and the page renders the same tool calls with its own components.

    python agent.py              # terminal surface
    python agent.py --web        # web surface on http://127.0.0.1:8061
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from common import scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from harness import Harness, Tool, Workspace  # noqa: E402

PORT = 8061
STR, NUMS, STRS = {"type": "string"}, {"type": "array", "items": {"type": "number"}}, {"type": "array", "items": {"type": "string"}}
SYSTEM = ("You are a coding agent with a data workspace. Read the files you need, then SHOW the answer with the UI tools "
          "(show_metric for key numbers, show_chart for series, show_table for lists). Finish with one sentence.")


def shown(**props):
    """A UI tool computes nothing: it acknowledges, and the surfaces draw the arguments."""
    return {"shown": True}


UI_TOOLS = [
    Tool("show_metric", "Show one key number.", {"type": "object", "properties": {"label": STR, "value": STR, "delta": STR},
         "required": ["label", "value"]}, shown, ui=True),
    Tool("show_chart", "Show a bar chart.", {"type": "object", "properties": {"title": STR, "labels": STRS, "values": NUMS},
         "required": ["title", "labels", "values"]}, shown, ui=True),
    Tool("show_table", "Show a table.", {"type": "object", "properties": {"columns": STRS, "rows": {"type": "array", "items": STRS}},
         "required": ["columns", "rows"]}, shown, ui=True),
]


def build_harness() -> Harness:
    return Harness(llm=get_llm(HERE / "fixtures"), system=SYSTEM, tools=Workspace().tools() + UI_TOOLS, fixture="session")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--web", action="store_true", help="serve the web surface instead of printing to the terminal")
    cli.add_argument("--port", type=int, default=PORT)
    args = cli.parse_args()
    harness = build_harness()
    if args.web:
        from web import build_web
        build_web(harness, title="Lab 1 - UI tools in the agent loop", mode="static", prompt=scenario.DASHBOARD_PROMPT).serve(args.port)
    else:
        from surfaces import TerminalSurface
        term = TerminalSurface()
        harness.on(term).run(scenario.DASHBOARD_PROMPT)
        print(term.text())
