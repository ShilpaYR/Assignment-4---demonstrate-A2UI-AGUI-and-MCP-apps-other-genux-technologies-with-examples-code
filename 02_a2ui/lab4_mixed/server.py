"""Part 2 / Lab 4 - A2UI, MIXED mode: two catalogs on one surface.

A2UI v1.0 lets one surface mix catalogs. The surface's default catalog is
the official Basic Catalog; exactly one component sets
``"@catalogId": "https://catalogs.genux.example/html/v1/catalog.json"`` and
is an ``HtmlFrame`` (the escape hatch from lab 3). Everything else is
declarative and data-bound.

The agent then uses all four agent-to-renderer messages:

* ``createSurface`` / ``updateComponents`` / ``updateDataModel`` - the first render;
* ``restock_beans`` action  -> ``updateDataModel`` *and* ``updateComponents``
  (the agent adds a receipt component to the live surface);
* ``apply_price`` action from the HtmlFrame -> ``updateDataModel`` on a Basic-Catalog KPI;
* ``close_surface`` action -> ``deleteSurface``.

    python server.py            # http://127.0.0.1:8024
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
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App, Response, sse_frame  # noqa: E402

PORT = 8024
SYSTEM = a2ui.catalog_prompt(with_html=True) + (
    "\nUse the basic catalog for the dashboard. Use exactly one HtmlFrame (with @catalogId) for a what-if "
    f"price calculator that emits apply_price.\nData:\n{scenario.as_text()}"
)

llm = get_llm(HERE / "fixtures")


def generate(prompt: str) -> list[dict]:
    msgs = a2ui.parse_jsonl(llm.text(system=SYSTEM, user=prompt, fixture="dashboard_mixed"))
    errors = a2ui.validate_stream(msgs, with_html=True)
    frames = [c for m in msgs for c in (m.get("updateComponents") or {}).get("components", []) if c.get("component") == "HtmlFrame"]
    if len(frames) > 1:
        errors.append("at most one HtmlFrame is allowed")
    for f in frames:
        if f.get("@catalogId") != a2ui.HTML_CATALOG_ID:
            errors.append(f"HtmlFrame {f['id']!r} must set @catalogId to the HTML catalog")
        errors += [f"HtmlFrame {f['id']!r}: {p}" for p in check_html(f.get("html", ""))]
    if errors:
        raise ValueError("; ".join(errors))
    return msgs


def frames(prompt: str):
    for m in generate(prompt):
        if stream_delay():
            time.sleep(stream_delay() * 40)
        yield sse_frame(m)


def handle_action(msg: dict) -> list[dict]:
    errors = a2ui.validate_action(msg)
    if errors:
        return [{"error": errors}]
    act, sid = msg["action"], msg["action"]["surfaceId"]
    ctx, name = act["context"], act["name"]
    if name == "restock_beans":
        beans = float(ctx["beansNow"]) + float(ctx["kg"])
        out = [
            a2ui.update_data_model(sid, "/inventory/beans_kg", beans),
            # structure can change too: the agent adds a receipt component to the live surface
            a2ui.update_components(sid, [
                {"id": "stock_col", "component": "Column", "children": ["stock_text", "restock_btn", "stock_status", "receipt"]},
                {"id": "receipt", "component": "Text", "text": f"**Receipt** - {ctx['kg']} kg ordered, ${float(ctx['kg']) * 18:.2f}, arriving Thursday."},
            ]),
        ]
    elif name == "apply_price" and act["sourceComponentId"] == "whatif":
        price = ctx.get("price")
        if not isinstance(price, (int, float)) or not 2 <= price <= 7:
            return [a2ui.update_data_model(sid, "/whatif/status", "Ignored an invalid price.")]
        out = [a2ui.update_data_model(sid, "/kpis/ticket", f"${price:.2f}"),
               a2ui.update_data_model(sid, "/whatif/status", f"Avg ticket KPI updated to ${price:.2f} by the agent.")]
    elif name == "close_surface":
        out = [a2ui.delete_surface(sid)]
    else:
        return [{"error": [f"unknown action {name!r}"]}]
    for m in out:
        assert not a2ui.validate_message(m, with_html=True)
    return out


def build_app() -> App:
    app = App(HERE / "page", title="A2UI lab 4 (mixed)")
    app.mount("a2ui", SHARED / "web")

    @app.post("/a2ui/stream")
    def a2ui_stream(req):
        return SSE(frames((req.json() or {}).get("prompt") or scenario.MIXED_PROMPT))

    @app.post("/a2ui/action")
    def a2ui_action(req):
        out = handle_action(req.json())
        return Response(json.dumps(out), 400 if "error" in out[0] else 200, "application/json")

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
