"""Part 1 / Lab 1 - AG-UI, STATIC mode.

Static generative UI: the components already exist in the page (a metric
card, a bar chart, a table). The agent does not design anything. It only
*chooses* which component to show and *fills in* its props, by calling a
tool such as ``show_metric(label, value, delta)``.

AG-UI carries those choices as typed events over Server-Sent Events:

    RUN_STARTED
    TEXT_MESSAGE_START / TEXT_MESSAGE_CONTENT / TEXT_MESSAGE_END
    TOOL_CALL_START(show_metric) / TOOL_CALL_ARGS (JSON, in chunks) / TOOL_CALL_END
    ... one block per component ...
    RUN_FINISHED

The page maps each tool name to a hand-written renderer.

    python server.py            # http://127.0.0.1:8011
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))  # repo root, for common/

from ag_ui.core import (  # noqa: E402  (official AG-UI Python SDK)
    EventType, RunAgentInput, RunFinishedEvent, RunStartedEvent, TextMessageContentEvent,
    TextMessageEndEvent, TextMessageStartEvent, ToolCallArgsEvent, ToolCallEndEvent, ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder  # noqa: E402

from common import scenario  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.web import SSE, App  # noqa: E402

PORT = 8011

# The three pre-built components, offered to the model as function-calling tools.
TOOLS = [
    {"name": "show_metric", "description": "Show one key number on a metric card.",
     "parameters": {"type": "object", "required": ["label", "value"], "properties": {
         "label": {"type": "string"}, "value": {"type": "string"}, "delta": {"type": "string"}}}},
    {"name": "show_chart", "description": "Show a bar chart. labels and values have the same length.",
     "parameters": {"type": "object", "required": ["title", "labels", "values"], "properties": {
         "title": {"type": "string"}, "labels": {"type": "array", "items": {"type": "string"}},
         "values": {"type": "array", "items": {"type": "number"}}}}},
    {"name": "show_table", "description": "Show a table; every row has one cell per column.",
     "parameters": {"type": "object", "required": ["columns", "rows"], "properties": {
         "columns": {"type": "array", "items": {"type": "string"}},
         "rows": {"type": "array", "items": {"type": "array", "items": {"type": "string"}}}}}},
]
TOOL_NAMES = {t["name"] for t in TOOLS}

SYSTEM = (
    "You are the analytics assistant of a coffee cart. Answer with one short sentence, "
    "then call show_metric, show_chart and show_table to display the data. "
    f"Data:\n{scenario.as_text()}\nDaily revenue: {dict(zip(scenario.week_labels(), scenario.week_revenue()))}"
)

llm = get_llm(HERE / "fixtures")
encoder = EventEncoder()


def check_args(name: str, args: dict) -> list[str]:
    """The page must never receive a component it cannot draw: check before sending."""
    if name not in TOOL_NAMES:
        return [f"unknown tool {name}"]
    schema = next(t for t in TOOLS if t["name"] == name)["parameters"]
    return [f"{name}: missing {p}" for p in schema["required"] if p not in args]


def run(inp: RunAgentInput):
    """One agent run as a generator of AG-UI events."""
    yield RunStartedEvent(type=EventType.RUN_STARTED, thread_id=inp.thread_id, run_id=inp.run_id)
    user_text = next((m.content for m in reversed(inp.messages) if m.role == "user"), scenario.DASHBOARD_PROMPT)
    reply = llm.chat(messages=[{"role": "system", "content": SYSTEM}, {"role": "user", "content": user_text}],
                     tools=TOOLS, fixture="dashboard")

    if reply["content"]:
        mid = f"msg_{uuid.uuid4().hex[:8]}"
        yield TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=mid, role="assistant")
        yield TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=mid, delta=reply["content"])
        yield TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=mid)

    for call in reply["tool_calls"]:
        if check_args(call["name"], call["arguments"]):
            continue  # drop anything the page cannot render
        yield ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=call["id"], tool_call_name=call["name"])
        args = json.dumps(call["arguments"])
        for i in range(0, len(args), 40):  # arguments stream as JSON text, like a model streams them
            yield ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=call["id"], delta=args[i:i + 40])
        yield ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=call["id"])

    yield RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=inp.thread_id, run_id=inp.run_id)


def build_app() -> App:
    app = App(HERE / "page", title="AG-UI lab 1 (static)")

    @app.post("/agui")
    def agui(req):
        inp = RunAgentInput.model_validate(req.json())  # the official input schema
        return SSE(encoder.encode(e) for e in run(inp))

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
