"""Offline tests for AG-UI lab 4 (mixed)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, post_sse, start  # noqa: E402
from common.jsonpatch import apply  # noqa: E402
import server  # noqa: E402

TOOLS = [{"name": "confirm_restock", "description": "approve", "parameters": {"type": "object"}}]
URL = None


def call(**kw):
    global URL
    URL = URL or start(server.build_app()) + "/agui"
    return post_sse(URL, agui_input("x", tools=TOOLS, **kw))


def first_state():
    return next(e for e in call() if e["type"] == "STATE_SNAPSHOT")["snapshot"]


def test_hybrid_layout_has_exactly_one_generated_view():
    types = [el["type"] for el in first_state()["ui"]["elements"].values()]
    assert types.count("GeneratedView") == 1 and "Metric" in types and "Button" in types


def test_button_action_triggers_a_client_tool_call_and_the_run_waits():
    ev = call(state=first_state(), forwarded={"action": "restock_beans", "params": {"kg": 10}})
    assert [e["toolCallName"] for e in ev if e["type"] == "TOOL_CALL_START"] == ["confirm_restock"]
    assert not any(e["type"] == "STATE_DELTA" for e in ev)  # nothing changes before the human answers


def test_approved_tool_result_patches_state():
    state = first_state()
    msgs = [{"id": "a", "role": "assistant", "toolCalls": [{"id": "c1", "type": "function",
             "function": {"name": "confirm_restock", "arguments": json.dumps({"kg": 10, "cost_usd": 180})}}]},
            {"id": "t", "role": "tool", "toolCallId": "c1", "content": json.dumps({"approved": True})}]
    ev = call(messages=msgs, state=state)
    new = apply(state, next(e for e in ev if e["type"] == "STATE_DELTA")["delta"])
    assert new["inventory"]["beans_kg"] == 13.5


def test_rejected_tool_result_changes_nothing():
    msgs = [{"id": "a", "role": "assistant", "toolCalls": [{"id": "c1", "type": "function",
             "function": {"name": "confirm_restock", "arguments": "{\"kg\": 10}"}}]},
            {"id": "t", "role": "tool", "toolCallId": "c1", "content": "{\"approved\": false}"}]
    assert not any(e["type"] == "STATE_DELTA" for e in call(messages=msgs, state=first_state()))


def test_sandbox_events_are_validated():
    good = call(state=first_state(), forwarded={"action": "apply_price", "params": {"price": 3.95}})
    bad = call(state=first_state(), forwarded={"action": "apply_price", "params": {"price": "DROP TABLE"}})
    assert any(e["type"] == "STATE_DELTA" for e in good)
    assert not any(e["type"] == "STATE_DELTA" for e in bad)


def test_unknown_actions_end_the_run_with_an_error_and_no_finish():
    ev = call(state=first_state(), forwarded={"action": "delete_database"})
    assert ev[-1]["type"] == "RUN_ERROR" and not any(e["type"] == "RUN_FINISHED" for e in ev)
