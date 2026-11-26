"""Part 1 / Lab 3 - AG-UI, OPEN-ENDED mode.

Open-ended generative UI: no catalog. The model writes a complete HTML/CSS/JS
document for something no pre-built component covers (an interactive
break-even calculator). Freedom has two costs: many more tokens, and code
the application must not trust.

The event stream:

    RUN_STARTED
    TEXT_MESSAGE_START / TEXT_MESSAGE_CONTENT x N / TEXT_MESSAGE_END   the raw HTML, streamed
    ACTIVITY_SNAPSHOT  activityType="genux.sandboxed_html"              policy verdict + final document
    RUN_FINISHED

ACTIVITY_SNAPSHOT is AG-UI's event for non-chat "activity" content such as
generated UI. The page mounts the document in a sandboxed iframe only after
the server-side policy check passes.

    python server.py            # http://127.0.0.1:8013
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from ag_ui.core import (  # noqa: E402
    ActivitySnapshotEvent, EventType, RunAgentInput, RunFinishedEvent, RunStartedEvent,
    TextMessageContentEvent, TextMessageEndEvent, TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder  # noqa: E402

from common import scenario, tokens  # noqa: E402
from common.llm import get_llm, strip_fences  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App  # noqa: E402

PORT = 8013

SYSTEM = """You write ONE self-contained HTML document for an interactive widget.
Rules:
- Inline <style> and <script> only. No external scripts, stylesheets, fonts, images or network calls.
- The document runs in a sandbox. To send a result to the app call genux.emit(name, payload).
  The only event the app accepts is "apply_price" with payload {"price": number}.
- Keep it under 300 lines. Output the HTML only, no markdown fences, no explanation.
""" + f"Context: this week the cart sold {scenario.kpis()['cups']} cups at an average of ${scenario.kpis()['avg_ticket']}."

llm = get_llm(HERE / "fixtures")
encoder = EventEncoder()


def run(inp: RunAgentInput):
    yield RunStartedEvent(type=EventType.RUN_STARTED, thread_id=inp.thread_id, run_id=inp.run_id)
    user_text = next((m.content for m in reversed(inp.messages) if m.role == "user"), scenario.WIDGET_PROMPT)

    # 1. stream the model's HTML as an ordinary text message (the page shows the source growing)
    mid = f"msg_{uuid.uuid4().hex[:8]}"
    yield TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=mid, role="assistant")
    parts = []
    for chunk in llm.stream(system=SYSTEM, user=user_text, fixture="break_even"):
        parts.append(chunk)
        yield TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=mid, delta=chunk)
    yield TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=mid)

    # 2. check the finished document, then hand it over as an activity the page can mount
    html = strip_fences("".join(parts))
    problems = check_html(html)
    yield ActivitySnapshotEvent(
        type=EventType.ACTIVITY_SNAPSHOT, message_id=f"act_{mid}", activity_type="genux.sandboxed_html",
        content={"status": "rejected" if problems else "ready", "problems": problems,
                 "title": "Break-even calculator", "html": "" if problems else html,
                 "tokens": tokens.count(html), "token_method": tokens.method(),
                 "allowedEvents": ["apply_price"]},
    )
    yield RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=inp.thread_id, run_id=inp.run_id)


def build_app() -> App:
    app = App(HERE / "page", title="AG-UI lab 3 (open-ended)")

    @app.post("/agui")
    def agui(req):
        return SSE(encoder.encode(e) for e in run(RunAgentInput.model_validate(req.json())))

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
