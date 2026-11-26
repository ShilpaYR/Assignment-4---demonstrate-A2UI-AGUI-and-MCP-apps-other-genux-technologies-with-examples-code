"""Part 3 / Lab 4 - json-render, MIXED mode: hybrid catalog, actions, and a second renderer.

The hybrid catalog (``hybridCatalog`` in ``shared/catalog.mjs``) is the base
catalog plus one ``HtmlBlock``. The model streams one SpecStream that uses
both, plus state and bindings:

* ``Metric`` and ``Text`` read ``{"$state": ...}`` so the agent can update them
  with small ``/state`` patches instead of re-sending elements;
* a ``Button`` uses the built-in ``setState`` action (runs in the page only);
* the ``restock_beans`` Button and the HtmlBlock's ``apply_price`` event are
  custom actions answered by the server with ``/state`` patches.

Then the json-render promise - one spec, many renderers: ``GET /jr/terminal``
draws the *same* spec with ``rich`` (``shared/terminal.py``). The HtmlBlock
degrades to a placeholder there; every catalog component survives.

    python server.py            # http://127.0.0.1:8034
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

import jr  # noqa: E402
import terminal  # noqa: E402
from common import jsonpatch, scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App, Response, sse_frame  # noqa: E402

PORT = 8034
SYSTEM = jr.prompt("hybrid") + f"\n\nDATA:\n{scenario.as_text()}"
llm = get_llm(HERE / "fixtures")
CURRENT = {"spec": None}            # last generated spec, for the terminal renderer


def check_op(op: dict, cat: dict) -> list[str]:
    if op["path"].startswith("/elements/"):
        el = op["value"]
        errors = jr.validate_element(op["path"].split("/", 2)[2], el, cat)
        if el.get("type") == "HtmlBlock":
            errors += check_html(el["props"].get("html", ""))
        return errors
    return []


def stream(prompt: str):
    cat, spec, blocks = jr.catalog("hybrid"), {}, 0
    for line in llm.text(system=SYSTEM, user=prompt, fixture="dashboard_hybrid").splitlines():
        op = jr.parse_patch_line(line)
        if not op:
            continue
        errors = check_op(op, cat)
        blocks += op["path"].startswith("/elements/") and op["value"].get("type") == "HtmlBlock"
        if blocks > 1:
            errors.append("only one HtmlBlock is allowed")
        if errors:
            yield sse_frame({"rejected": op["path"], "errors": errors}, event="genux")
            continue
        spec = jsonpatch.apply(spec, [op])
        yield sse_frame(op)
    CURRENT["spec"] = spec


def handle_action(body: dict) -> list[dict]:
    """Custom actions: validate, then answer with /state patches."""
    action, params, state = body.get("action"), body.get("params") or {}, body.get("state") or {}
    if action == "restock_beans":
        beans = float(state.get("inventory", {}).get("beans_kg", 0)) + float(params.get("kg", 0))
        ops = [{"op": "replace", "path": "/state/inventory/beans_kg", "value": beans},
               {"op": "replace", "path": "/state/inventory/label", "value": f"Beans on hand: {beans:g} kg - order placed."}]
    elif action == "apply_price" and isinstance(params.get("price"), (int, float)) and 2 <= params["price"] <= 7:
        ops = [{"op": "replace", "path": "/state/kpis/ticket", "value": f"${params['price']:.2f}"},
               {"op": "replace", "path": "/state/whatif/status", "value": f"Avg ticket set to ${params['price']:.2f} by the server."}]
    else:
        return [{"error": f"refused action {action!r} with {params}"}]
    if CURRENT["spec"]:
        CURRENT["spec"] = jsonpatch.apply(CURRENT["spec"], ops)
    return ops


def build_app() -> App:
    app = App(HERE / "page", title="json-render lab 4 (mixed)")
    app.mount("jr", SHARED / "web")

    @app.post("/jr/stream")
    def jr_stream(req):
        return SSE(stream((req.json() or {}).get("prompt") or scenario.MIXED_PROMPT))

    @app.post("/jr/action")
    def action(req):
        return handle_action(req.json())

    @app.get("/jr/terminal")
    def term(req):                   # the second renderer: same spec, drawn as text
        if not CURRENT["spec"]:
            list(stream(scenario.MIXED_PROMPT))
        return Response(terminal.to_text(CURRENT["spec"]), 200, "text/plain; charset=utf-8")

    @app.get("/jr/spec")
    def current(req):
        return Response(json.dumps(CURRENT["spec"]), 200, "application/json")

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
