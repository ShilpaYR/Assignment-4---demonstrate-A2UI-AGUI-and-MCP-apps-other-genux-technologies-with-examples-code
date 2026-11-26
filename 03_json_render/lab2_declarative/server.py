"""Part 3 / Lab 2 - json-render, DECLARATIVE mode: the model streams SpecStream patches.

This is json-render's native generation format. The system prompt is
exactly what the library generates from the catalog (``catalog.prompt()``,
saved in ``shared/generated/prompt_base.txt``). The model answers with JSONL,
one RFC 6902 patch per line:

    {"op":"add","path":"/root","value":"dash"}
    {"op":"add","path":"/elements/dash","value":{"type":"Card","props":{...},"children":["kpis",...]}}
    ...

The server validates **each line as soon as it is complete** (component
name, Zod-derived prop schema, allowed actions) and forwards it, so the page
paints the first element long before the model is done. An invalid line -
the scripted reply contains a hallucinated ``PieChart`` - is dropped and
reported; the rest of the UI is unaffected.

    python server.py            # http://127.0.0.1:8032
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

import jr  # noqa: E402
from common import jsonpatch, scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.web import SSE, App, sse_frame  # noqa: E402

PORT = 8032
SYSTEM = jr.prompt("base") + f"\n\nDATA:\n{scenario.as_text()}\nDaily revenue: {dict(zip(scenario.week_labels(), scenario.week_revenue()))}"
llm = get_llm(HERE / "fixtures")


def check_op(op: dict, cat: dict) -> list[str]:
    """Validate one patch the moment it arrives."""
    if op["path"].startswith("/elements/") and op["op"] in ("add", "replace"):
        return jr.validate_element(op["path"].split("/", 2)[2], op["value"], cat)
    if op["path"] == "/root" or op["path"].startswith("/state"):
        return []
    return [f"unexpected patch path {op['path']}"]


def lines(chunks):
    """Re-cut a stream of text chunks into complete lines (a complete line = a complete patch)."""
    buffer = ""
    for chunk in chunks:
        buffer += chunk
        while "\n" in buffer:
            line, buffer = buffer.split("\n", 1)
            yield line
    if buffer.strip():
        yield buffer


def stream(prompt: str):
    """Yield (kind, payload): ("op", patch) for accepted lines, ("meta", info) for reports."""
    cat, spec, rejected = jr.catalog("base"), {"root": None, "elements": {}, "state": {}}, []
    t0 = time.perf_counter()
    first = None
    for line in lines(llm.stream(system=SYSTEM, user=prompt, fixture="dashboard")):
        try:
            op = jr.parse_patch_line(line)
        except (ValueError, json.JSONDecodeError) as exc:
            rejected.append(str(exc))
            yield "meta", {"rejected": line[:120], "errors": [str(exc)]}
            continue
        if op is None:
            continue
        errors = check_op(op, cat)
        if errors:
            rejected.append(op["path"])
            yield "meta", {"rejected": op["path"], "errors": errors}
            continue
        spec = jsonpatch.apply(spec, [op])
        if first is None and op["path"].startswith("/elements/"):
            first = time.perf_counter() - t0
        yield "op", op
    issues = jr.validate(spec, "base")                  # whole-spec checks: dangling children, root
    yield "meta", {"done": True, "elements": len(spec["elements"]), "rejected": rejected, "issues": issues,
                   "server_first_element_ms": round(1000 * (first or 0), 1), "server_total_ms": round(1000 * (time.perf_counter() - t0), 1)}


def build_app() -> App:
    app = App(HERE / "page", title="json-render lab 2 (declarative)")
    app.mount("jr", SHARED / "web")

    @app.post("/jr/stream")
    def jr_stream(req):
        prompt = (req.json() or {}).get("prompt") or scenario.DASHBOARD_PROMPT
        return SSE(sse_frame(v, event=None if k == "op" else "genux") for k, v in stream(prompt))

    @app.post("/jr/action")
    def action(req):
        body = req.json()
        if body.get("action") != "restock_beans":
            return [{"error": "unknown action"}]
        return [{"op": "replace", "path": "/elements/beans/props/text", "value": f"Ordered {body['params']['kg']} kg of beans."}]

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
