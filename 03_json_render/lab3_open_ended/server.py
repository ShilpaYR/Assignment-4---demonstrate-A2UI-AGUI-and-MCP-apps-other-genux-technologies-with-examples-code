"""Part 3 / Lab 3 - json-render, OPEN-ENDED mode: a catalog with only HtmlBlock.

The catalog shrinks to one component, ``HtmlBlock(title, html, caption)``
(defined in ``shared/catalog.mjs`` as ``htmlCatalog``). The model still
answers in json-render's SpecStream format, but the single element it adds
carries a whole model-written HTML document.

json-render's machinery still applies around the free-form region:
* ``caption`` is a ``{"$state": "/status"}`` expression;
* the element's ``on`` map decides which events may leave the sandbox:
  ``"on": {"apply_price": {"action": "apply_price"}}`` - the renderer drops
  every other ``genux.emit`` name;
* the action goes to the server, which answers with a ``/state`` patch.

    python server.py            # http://127.0.0.1:8033
"""

from __future__ import annotations

import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

import jr  # noqa: E402
from common import scenario, tokens  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App, sse_frame  # noqa: E402

PORT = 8033
SYSTEM = jr.prompt("html")
llm = get_llm(HERE / "fixtures")


def patches(prompt: str) -> list[dict]:
    text = llm.text(system=SYSTEM, user=prompt, fixture="widget")
    ops = [op for op in map(jr.parse_patch_line, text.splitlines()) if op]
    spec = jr.apply_stream(text)
    errors = jr.validate(spec, "html")
    for eid, el in spec["elements"].items():
        errors += [f"{eid}: {p}" for p in check_html(el["props"].get("html", ""))]
    if errors:
        raise ValueError("; ".join(errors))
    return ops


def handle_action(body: dict) -> list[dict]:
    price = (body.get("params") or {}).get("price")
    if body.get("action") != "apply_price" or not isinstance(price, (int, float)) or not 2 <= price <= 7:
        return [{"op": "replace", "path": "/state/status", "value": "Ignored an invalid event from the HtmlBlock."}]
    return [{"op": "replace", "path": "/state/status", "value": f"Server stored list price ${price:.2f}."}]


def build_app() -> App:
    app = App(HERE / "page", title="json-render lab 3 (open-ended)")
    app.mount("jr", SHARED / "web")

    @app.post("/jr/stream")
    def stream(req):
        return SSE(sse_frame(op) for op in patches((req.json() or {}).get("prompt") or scenario.WIDGET_PROMPT))

    @app.post("/jr/action")
    def action(req):
        return handle_action(req.json())

    @app.get("/jr/tokens")
    def token_report(req):
        html = jr.apply_stream(llm.text(system=SYSTEM, user="", fixture="widget"))["elements"]["widget"]["props"]["html"]
        return {"html_tokens": tokens.count(html), "method": tokens.method()}

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
