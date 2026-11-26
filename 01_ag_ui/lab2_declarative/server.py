"""Part 1 / Lab 2 - AG-UI, DECLARATIVE mode.

Declarative generative UI: the agent designs the *layout*, but only from a
catalog of allowed components (Card, Row, Metric, BarChart, Table, ...). It
writes a flat element map; the application validates it; the page renders it.

AG-UI's way to carry a declarative UI is **shared state**. The UI spec lives
in the agent state under ``state.ui``:

    STATE_SNAPSHOT  {"ui": {"root": null, "elements": {}}}     an empty canvas
    STATE_DELTA     [{"op":"add","path":"/ui/root","value":"dash"}]          RFC 6902
    STATE_DELTA     [{"op":"add","path":"/ui/elements/dash","value":{...}}]
    ...

Each delta adds one element, parent first, so the page paints the frame
before the details arrive. STEP_STARTED / STEP_FINISHED mark the
generate -> validate -> publish pipeline.

    python server.py            # http://127.0.0.1:8012
"""

from __future__ import annotations

import argparse
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from ag_ui.core import (  # noqa: E402
    EventType, RunAgentInput, RunErrorEvent, RunFinishedEvent, RunStartedEvent, StateDeltaEvent,
    StateSnapshotEvent, StepFinishedEvent, StepStartedEvent, TextMessageContentEvent, TextMessageEndEvent,
    TextMessageStartEvent,
)
from ag_ui.encoder import EventEncoder  # noqa: E402

from common import scenario  # noqa: E402
from common.catalog import catalog_prompt, parse_json_reply, spec_to_patches, validate_spec  # noqa: E402
from common.llm import get_llm, stream_delay  # noqa: E402
from common.web import SSE, App  # noqa: E402

PORT = 8012

# The system prompt is generated from the catalog: prompt and validator cannot drift apart.
SYSTEM = catalog_prompt() + f"\n\nData for the dashboard:\n{scenario.as_text()}\n" \
    f"Daily revenue: {dict(zip(scenario.week_labels(), scenario.week_revenue()))}"

llm = get_llm(HERE / "fixtures")
encoder = EventEncoder()


def say(text: str):
    mid = f"msg_{uuid.uuid4().hex[:8]}"
    yield TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=mid, role="assistant")
    yield TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=mid, delta=text)
    yield TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=mid)


def run(inp: RunAgentInput):
    yield RunStartedEvent(type=EventType.RUN_STARTED, thread_id=inp.thread_id, run_id=inp.run_id)
    user_text = next((m.content for m in reversed(inp.messages) if m.role == "user"), scenario.DASHBOARD_PROMPT)

    # 1. generate: the model writes a whole layout as JSON
    yield StepStartedEvent(type=EventType.STEP_STARTED, step_name="generate")
    reply = "".join(llm.stream(system=SYSTEM, user=user_text, fixture="dashboard_spec"))
    yield StepFinishedEvent(type=EventType.STEP_FINISHED, step_name="generate")

    # 2. validate: nothing reaches the page unless the catalog allows it
    yield StepStartedEvent(type=EventType.STEP_STARTED, step_name="validate")
    try:
        spec = parse_json_reply(reply)
        errors = validate_spec(spec)
    except ValueError as exc:
        spec, errors = None, [f"reply is not JSON: {exc}"]
    yield StepFinishedEvent(type=EventType.STEP_FINISHED, step_name="validate")
    if errors:
        yield RunErrorEvent(type=EventType.RUN_ERROR, message="; ".join(errors[:5]), code="INVALID_UI_SPEC")
        return

    # 3. publish: the UI becomes agent state, one element per delta
    yield StepStartedEvent(type=EventType.STEP_STARTED, step_name="publish")
    yield StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot={"ui": {"root": None, "elements": {}}})
    for op in spec_to_patches(spec):
        op = {**op, "path": "/ui" + op["path"]}
        if stream_delay():
            import time
            time.sleep(stream_delay() * 20)  # slow enough to watch the canvas fill in
        yield StateDeltaEvent(type=EventType.STATE_DELTA, delta=[op])
    yield StepFinishedEvent(type=EventType.STEP_FINISHED, step_name="publish")
    yield from say(f"Built a {len(spec['elements'])}-element dashboard from the catalog.")
    yield RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=inp.thread_id, run_id=inp.run_id)


def build_app() -> App:
    app = App(HERE / "page", title="AG-UI lab 2 (declarative)")

    @app.post("/agui")
    def agui(req):
        return SSE(encoder.encode(e) for e in run(RunAgentInput.model_validate(req.json())))

    @app.get("/catalog")
    def show_catalog(req):
        return {"prompt": SYSTEM}

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
