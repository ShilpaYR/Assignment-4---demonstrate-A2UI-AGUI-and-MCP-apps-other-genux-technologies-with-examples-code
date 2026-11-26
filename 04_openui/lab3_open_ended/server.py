"""Part 4 / Lab 3 - OpenUI Lang, OPEN-ENDED mode: HtmlArtifact only.

OpenUI's own answer to open-ended UI is the ``HtmlArtifact`` pattern (see the
"html-artifact" example in the OpenUI repository): a component whose
argument is a complete HTML document. The library here contains only
``Stack`` and ``HtmlArtifact(title, document)``, so the whole answer is

    root = Stack([calc])
    calc = HtmlArtifact("Break-even calculator", "<!doctype html>...")

The document is a JSON-style string literal inside the program. While it
streams, the official parser reports the element as *partial*; the page
shows a progress label and mounts the sandbox only when the string is
closed, so half a document never runs.

    python server.py            # http://127.0.0.1:8043
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

PORT = 8043
LIBRARY = "html"
SYSTEM = oui.prompt(LIBRARY) + f"\n\nData:\n{scenario.as_text()}\nDaily revenue: {scenario.week_revenue()}"
llm = get_llm(HERE / "fixtures")


def frames(prompt: str):
    text = ""
    for chunk in llm.stream(system=SYSTEM, user=prompt, fixture="calculator"):
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
    """Events from the artifact are untrusted: check name and payload."""
    price = (body.get("params") or {}).get("price")
    if body.get("action") != "apply_price" or not isinstance(price, (int, float)) or not 2 <= price <= 7:
        return {"error": f"refused {body.get('action')!r} with {body.get('params')}"}
    return {"message": f"Server stored list price ${price:.2f}."}


def build_app() -> App:
    app = App(HERE / "page", title="OpenUI lab 3 (open-ended)")
    app.mount("oui", SHARED)

    @app.post("/oui/stream")
    def stream(req):
        return SSE(frames((req.json() or {}).get("prompt") or scenario.WIDGET_PROMPT))

    @app.post("/oui/action")
    def action(req):
        return handle_action(req.json())

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
