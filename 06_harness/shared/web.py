"""The web surface's HTTP app, shared by the four harness labs.

    POST /agui   RunAgentInput  -> SSE of AG-UI events produced by the harness run
                 forwardedProps.action (lab 4) becomes the next user turn: "[ui action] name {params}"
    GET  /config                -> page settings (title, mode, prompt)
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

SHARED = Path(__file__).resolve().parent
sys.path[:0] = [str(SHARED.parents[1]), str(SHARED)]

from ag_ui.core import RunAgentInput  # noqa: E402

from common.web import SSE, App  # noqa: E402
from surfaces import stream_run  # noqa: E402


def build_web(harness, *, title: str, mode: str, prompt: str, actions: set[str] | None = None) -> App:
    app = App(SHARED / "web", title=f"harness web surface: {title}")

    @app.get("/config")
    def config(req):
        return {"part": "Part 6 · Harness integration", "title": title, "mode": mode, "prompt": prompt}

    @app.post("/agui")
    def agui(req):
        inp = RunAgentInput.model_validate(req.json())
        fp = inp.forwarded_props or {}
        if fp.get("action"):
            if fp["action"] not in (actions or set()):     # the page may only send allowed actions
                return {"error": f"action {fp['action']!r} not allowed"}
            text = f"[ui action] {fp['action']} {json.dumps(fp.get('params') or {})}"
        else:  # a fresh request starts a fresh conversation
            harness.messages.clear()
            text = next((m.content for m in reversed(inp.messages) if m.role == "user"), prompt)
        return SSE(stream_run(harness, text, inp.thread_id, inp.run_id))

    return app
