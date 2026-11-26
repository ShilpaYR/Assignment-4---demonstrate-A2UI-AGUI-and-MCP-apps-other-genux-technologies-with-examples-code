"""Part 1 / Lab 4 - AG-UI, MIXED (hybrid) mode.

The hybrid pattern: keep the catalog for everything it can express, and
allow exactly one escape hatch, a ``GeneratedView`` whose ``html`` prop is
model-written and runs in a sandbox. Then close the loop: the user's
clicks come back to the agent as new runs.

Three kinds of round trip, all over AG-UI:

1. **Catalog action** - the "Reorder beans" Button sends
   ``forwardedProps.action = "restock_beans"``.
2. **Client tool / human in the loop** - the agent answers by calling
   ``confirm_restock``, a tool the *page* declared in ``RunAgentInput.tools``.
   The page shows a dialog; the user's answer returns as a ``tool`` message
   in the next run; the agent then patches state (STATE_DELTA).
3. **Event from the sandbox** - the generated calculator calls
   ``genux.emit("apply_price", {...})``; the page forwards it as an action;
   the server validates it before touching state.

The server is stateless: the page sends the current state with every run
(``RunAgentInput.state``), exactly as AG-UI intends.

    python server.py            # http://127.0.0.1:8014
"""

from __future__ import annotations

import argparse
import json
import sys
import uuid
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from ag_ui.core import (  # noqa: E402
    EventType, RunAgentInput, RunErrorEvent, RunFinishedEvent, RunStartedEvent, StateDeltaEvent,
    StateSnapshotEvent, TextMessageContentEvent, TextMessageEndEvent, TextMessageStartEvent,
    ToolCallArgsEvent, ToolCallEndEvent, ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder  # noqa: E402

from common import scenario  # noqa: E402
from common.catalog import catalog_prompt, parse_json_reply, validate_spec  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.sandbox import check_html  # noqa: E402
from common.web import SSE, App  # noqa: E402

PORT = 8014
ACTIONS = {"restock_beans": "order more coffee beans (params: kg)"}
GENERATED_EVENTS = {"apply_price"}       # the only events the sandbox may send
BEAN_PRICE_PER_KG = 18.0

SYSTEM = catalog_prompt(hybrid=True, actions=ACTIONS) + (
    "\nUse GeneratedView at most once, only for the what-if price calculator. "
    "Inside it, call genux.emit('apply_price', {price}) when the user picks a price."
    f"\n\nData:\n{scenario.as_text()}"
)

llm = get_llm(HERE / "fixtures")
encoder = EventEncoder()


def say(text):
    mid = f"msg_{uuid.uuid4().hex[:8]}"
    yield TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=mid, role="assistant")
    yield TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=mid, delta=text)
    yield TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=mid)


def generate(user_text):
    """Turn 1: one hybrid layout - catalog components plus one sandboxed region."""
    spec = parse_json_reply(llm.text(system=SYSTEM, user=user_text, fixture="dashboard_hybrid"))
    errors = validate_spec(spec, hybrid=True, actions=set(ACTIONS))
    for eid, el in spec["elements"].items():
        if el["type"] == "GeneratedView":
            errors += [f"{eid}: {p}" for p in check_html(el["props"]["html"])]
    if errors:
        yield RunErrorEvent(type=EventType.RUN_ERROR, message="; ".join(errors[:5]), code="INVALID_UI_SPEC")
        return
    yield StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot={"ui": spec, "inventory": scenario.inventory()})
    yield from say("Here is the week. The purple region is a generated calculator; everything else is from the catalog.")


def ask_confirmation(inp, params):
    """The agent needs a human decision: it calls a tool that only the page can execute."""
    if "confirm_restock" not in {t.name for t in inp.tools or []}:
        yield RunErrorEvent(type=EventType.RUN_ERROR, message="page did not offer confirm_restock", code="NO_CLIENT_TOOL")
        return
    kg = max(1, min(int(params.get("kg", 10)), 50))
    call_id = f"call_{uuid.uuid4().hex[:8]}"
    yield from say(f"Reordering needs your approval: {kg} kg costs ${kg * BEAN_PRICE_PER_KG:.2f}.")
    yield ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=call_id, tool_call_name="confirm_restock")
    yield ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=call_id,
                            delta=json.dumps({"kg": kg, "cost_usd": kg * BEAN_PRICE_PER_KG}))
    yield ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=call_id)
    # the run ends here; the page runs the tool (shows a dialog) and starts the next run


def finish_restock(inp, tool_msg):
    """The client tool's result arrived as a `tool` message: act on it."""
    result = json.loads(tool_msg.content)
    call = next(tc for m in inp.messages if m.role == "assistant" for tc in (m.tool_calls or []) if tc.id == tool_msg.tool_call_id)
    kg = json.loads(call.function.arguments)["kg"]
    if not result.get("approved"):
        yield from say("Okay, no order placed.")
        return
    beans = round((inp.state or {}).get("inventory", {}).get("beans_kg", 0) + kg, 1)
    yield StateDeltaEvent(type=EventType.STATE_DELTA, delta=[
        {"op": "replace", "path": "/inventory/beans_kg", "value": beans},
        {"op": "replace", "path": "/ui/elements/note/props/text", "value": f"Beans on hand: {beans} kg - order of {kg} kg placed."},
        {"op": "replace", "path": "/ui/elements/restock/props/label", "value": "Reorder again"},
    ])
    yield from say(f"Order placed. Beans on hand will be {beans} kg.")


def apply_price(params):
    """An event that came out of the sandbox. Treat it as untrusted input."""
    price = params.get("price")
    if not isinstance(price, (int, float)) or not 2 <= price <= 7:
        yield from say("Ignored an invalid price from the calculator.")
        return
    yield StateDeltaEvent(type=EventType.STATE_DELTA, delta=[
        {"op": "replace", "path": "/ui/elements/m-ticket/props/value", "value": f"${price:.2f}"},
        {"op": "add", "path": "/ui/elements/m-ticket/props/delta", "value": "new list price"},
    ])
    yield from say(f"List price set to ${price:.2f} (from the generated calculator).")


def run(inp: RunAgentInput):
    yield RunStartedEvent(type=EventType.RUN_STARTED, thread_id=inp.thread_id, run_id=inp.run_id)
    failed = False
    for event in route(inp):
        failed = failed or isinstance(event, RunErrorEvent)
        yield event
    if not failed:  # RUN_ERROR already ends a run; never follow it with RUN_FINISHED
        yield RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=inp.thread_id, run_id=inp.run_id)


def route(inp: RunAgentInput):
    """Decide what this run is: a tool result, a UI action, or a fresh request."""
    fp = inp.forwarded_props or {}
    last = inp.messages[-1] if inp.messages else None
    if fp.get("action") == "restock_beans":
        yield from ask_confirmation(inp, fp.get("params") or {})
    elif fp.get("action") in GENERATED_EVENTS:
        yield from apply_price(fp.get("params") or {})
    elif fp.get("action"):
        yield RunErrorEvent(type=EventType.RUN_ERROR, message=f"action {fp['action']!r} is not allowed", code="BAD_ACTION")
    elif last is not None and last.role == "tool":
        yield from finish_restock(inp, last)
    else:
        user_text = next((m.content for m in reversed(inp.messages) if m.role == "user"), scenario.MIXED_PROMPT)
        yield from generate(user_text)


def build_app() -> App:
    app = App(HERE / "page", title="AG-UI lab 4 (mixed)")

    @app.post("/agui")
    def agui(req):
        return SSE(encoder.encode(e) for e in run(RunAgentInput.model_validate(req.json())))

    return app


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
