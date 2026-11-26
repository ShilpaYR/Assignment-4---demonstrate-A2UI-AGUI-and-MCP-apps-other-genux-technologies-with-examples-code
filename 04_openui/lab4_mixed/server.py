"""Part 4 / Lab 4 - OpenUI Lang, MIXED mode: primitives + one HtmlArtifact + edits.

The hybrid library is the declarative primitives plus ``HtmlArtifact``. The
model composes the dashboard from primitives and adds one artifact for the
what-if calculator. Two kinds of user events come back:

* the ``restock_beans`` Button -> the server answers with an edit
  ``beans = Text(...)``;
* ``genux.emit("apply_price")`` inside the artifact -> the server validates
  the price and answers ``ticket = Metric("Avg ticket", "$4.20", ...)``.

The page merges edits with ``mergeStatements`` and re-renders only the
changed statements, so the artifact keeps its state. The demo also measures
how much of the answer's token budget the artifact consumes.

    python server.py            # http://127.0.0.1:8044
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
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App, sse_frame  # noqa: E402

PORT = 8044
LIBRARY = "hybrid"
SYSTEM = oui.prompt(LIBRARY) + f"\n\nData:\n{scenario.as_text()}\nDaily revenue: {scenario.week_revenue()}"
llm = get_llm(HERE / "fixtures")


def frames(prompt: str):
    text = ""
    for chunk in llm.stream(system=SYSTEM, user=prompt, fixture="dashboard_hybrid"):
        text += chunk
        yield sse_frame({"delta": chunk})
    errors = oui.check(text, LIBRARY)                 # the official parser, run once the program is complete
    docs = oui.artifact_documents(text, LIBRARY)
    errors += [f"HtmlArtifact: {p}" for d in docs for p in check_html(d)]   # the open-ended part gets the HTML policy
    if len(docs) > 1:
        errors.append("at most one HtmlArtifact is allowed")
    yield sse_frame({"done": True, "errors": errors, "statements": len(oui.statements(text)),
                     "tokens": tokens.count(text), "artifact_tokens": sum(tokens.count(d) for d in docs),
                     "token_method": tokens.method()}, event="genux")


def handle_action(body: dict) -> dict:
    """Answer user events with OpenUI edits: replacement statements for single elements."""
    action, params = body.get("action"), body.get("params") or {}
    if action == "restock_beans":
        beans = scenario.INVENTORY["beans_kg"] + 10
        return {"patch": f'beans = Text("Beans on hand: {beans} kg - 10 kg ordered.", "strong")\n'}
    price = params.get("price")
    if action == "apply_price" and isinstance(price, (int, float)) and 2 <= price <= 7:
        return {"patch": f'ticket = Metric("Avg ticket", "${price:.2f}", "new list price")\n'}
    return {"error": f"refused {action!r} with {params}"}


def build_app() -> App:
    app = App(HERE / "page", title="OpenUI lab 4 (mixed)")
    app.mount("oui", SHARED)

    @app.post("/oui/stream")
    def stream(req):
        return SSE(frames((req.json() or {}).get("prompt") or scenario.MIXED_PROMPT))

    @app.post("/oui/action")
    def action(req):
        return handle_action(req.json())

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
