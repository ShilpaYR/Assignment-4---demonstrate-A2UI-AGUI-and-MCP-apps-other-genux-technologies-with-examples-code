"""Part 4 / Lab 2 - OpenUI Lang, DECLARATIVE mode: composing primitives, streamed.

The library now holds primitives (Stack, Card, Row, Text, Metric, BarChart,
Table, Button) and the model composes the layout itself:

    root = Stack([dash])
    dash = Card("Campus Coffee Cart - this week", [kpis, chart, items, stock])
    kpis = Row([rev, cups, ticket])
    rev = Metric("Revenue", "$4,669.20", "+8.4%")
    ...

``dash`` refers to ``kpis`` before ``kpis`` is defined. That is OpenUI's
**forward reference** (hoisting): the parser keeps the reference as
"unresolved" and renders what it can; the page shows the pending names and
fills them in as their lines arrive. The format is line-oriented and has no
closing braces to wait for, which makes it compact and stream-friendly; the
demo measures it against JSON formats for the same dashboard.

    python server.py            # http://127.0.0.1:8042
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

import oui  # noqa: E402
from common import scenario, tokens  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.web import SSE, App, sse_frame  # noqa: E402

PORT = 8042
LIBRARY = "declarative"
SYSTEM = oui.prompt(LIBRARY) + f"\n\nData:\n{scenario.as_text()}\nDaily revenue: {scenario.week_revenue()}"
llm = get_llm(HERE / "fixtures")


def frames(prompt: str):
    text = ""
    for chunk in llm.stream(system=SYSTEM, user=prompt, fixture="dashboard"):
        text += chunk
        yield sse_frame({"delta": chunk})
    errors = oui.check(text, LIBRARY)                 # the official parser, run once the program is complete
    yield sse_frame({"done": True, "errors": errors, "statements": len(oui.statements(text)),
                     "tokens": tokens.count(text), "token_method": tokens.method()}, event="genux")


def handle_action(body: dict) -> dict:
    """Edits are statements: replace one line of the program, keep everything else."""
    if body.get("action") != "restock_beans":
        return {"error": f"unknown action {body.get('action')!r}"}
    beans = scenario.INVENTORY["beans_kg"] + 10
    return {"patch": f'beans = Text("Beans on hand: {beans} kg - 10 kg ordered.", "strong")\n'}


def build_app() -> App:
    app = App(HERE / "page", title="OpenUI lab 2 (declarative)")
    app.mount("oui", SHARED)

    @app.post("/oui/stream")
    def stream(req):
        return SSE(frames((req.json() or {}).get("prompt") or scenario.DASHBOARD_PROMPT))

    @app.post("/oui/action")
    def action(req):
        return handle_action(req.json())

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
