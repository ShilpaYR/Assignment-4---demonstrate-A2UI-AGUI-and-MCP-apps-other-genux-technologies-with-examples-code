"""Part 2 / Lab 3 - A2UI, OPEN-ENDED mode: a custom catalog with one HtmlFrame.

A2UI is declarative by design: the standard Basic Catalog has no component
that runs model-written code, and that is a deliberate safety property.
Open-ended generation is still possible, the A2UI way: a **custom catalog**.
``schema/genux_html_catalog.json`` defines one component, ``HtmlFrame``,
whose ``html`` property is a whole document the renderer sandboxes.

The surface's default catalog is that custom catalog, so the entire surface
is one model-written document. Everything else stays A2UI:

* the HTML travels inside a normal ``createSurface`` message;
* the frame's caption is bound to the data model (``{"@path": "/status"}``);
* ``genux.emit("apply_price", ...)`` inside the document becomes a standard
  A2UI ``action`` message with ``sourceComponentId = "root"``;
* the agent answers with ``updateDataModel``.

    python server.py            # http://127.0.0.1:8023
"""

from __future__ import annotations

import argparse
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
SHARED = HERE.parent / "shared"
sys.path[:0] = [str(HERE.parents[1]), str(SHARED)]

import a2ui  # noqa: E402
from common import scenario, tokens  # noqa: E402
from common.llm import get_llm, strip_fences  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App, Response, sse_frame  # noqa: E402

PORT = 8023
SURFACE = "break_even"
SYSTEM = (
    "Write ONE self-contained HTML document (inline CSS and JS only, no network). "
    "It runs in a sandbox; call genux.emit('apply_price', {price}) when the user picks a price. "
    "Output the HTML only."
)

llm = get_llm(HERE / "fixtures")


def surface_messages(prompt: str) -> list[dict]:
    html = strip_fences(llm.text(system=SYSTEM, user=prompt, fixture="break_even"))
    problems = check_html(html)
    if problems:
        raise ValueError("generated HTML rejected: " + "; ".join(problems))
    frame = {"id": "root", "component": "HtmlFrame", "title": "Break-even calculator", "html": html,
             "caption": {"@path": "/status"}, "allowedEvents": ["apply_price"]}
    msgs = [a2ui.create_surface(SURFACE, a2ui.HTML_CATALOG_ID, components=[frame],
                                data_model={"status": f"Model-written document, {tokens.count(html)} tokens. Waiting for a price."})]
    errors = a2ui.validate_stream(msgs, with_html=True)   # the custom catalog is part of validation
    if errors:
        raise ValueError("; ".join(errors))
    return msgs


def handle_action(msg: dict) -> list[dict]:
    errors = a2ui.validate_action(msg)
    if errors:
        return [{"error": errors}]
    act = msg["action"]
    price = act["context"].get("price")
    if act["name"] != "apply_price" or not isinstance(price, (int, float)) or not 2 <= price <= 7:
        return [a2ui.update_data_model(act["surfaceId"], "/status", "Ignored an invalid event from the frame.")]
    return [a2ui.update_data_model(act["surfaceId"], "/status",
                                   f"Agent received price ${price:.2f} (break-even at {act['context'].get('breakEvenCups')} cups/week).")]


def build_app() -> App:
    app = App(HERE / "page", title="A2UI lab 3 (open-ended)")
    app.mount("a2ui", SHARED / "web")

    @app.post("/a2ui/stream")
    def a2ui_stream(req):
        return SSE(sse_frame(m) for m in surface_messages((req.json() or {}).get("prompt") or scenario.WIDGET_PROMPT))

    @app.post("/a2ui/action")
    def a2ui_action(req):
        out = handle_action(req.json())
        return Response(json.dumps(out), 400 if "error" in out[0] else 200, "application/json")

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
