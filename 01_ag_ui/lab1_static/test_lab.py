"""Offline tests for AG-UI lab 1 (static). No model, no network: ScriptedLLM replays fixtures/."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from ag_ui.core import RunAgentInput  # noqa: E402
from common.demo import agui_input, post_sse, start  # noqa: E402
import server  # noqa: E402


def events():
    return post_sse(f"{start(server.build_app())}/agui", agui_input("dashboard please"))


def test_run_is_bracketed_by_started_and_finished():
    ev = events()
    assert ev[0]["type"] == "RUN_STARTED" and ev[-1]["type"] == "RUN_FINISHED"


def test_every_tool_call_is_a_known_component_with_valid_json_args():
    ev = events()
    args = {}
    for e in ev:
        if e["type"] == "TOOL_CALL_START":
            assert e["toolCallName"] in server.TOOL_NAMES
            args[e["toolCallId"]] = ""
        elif e["type"] == "TOOL_CALL_ARGS":
            args[e["toolCallId"]] += e["delta"]
    parsed = [json.loads(a) for a in args.values()]
    assert len(parsed) == 5 and parsed[0]["label"] == "Revenue"


def test_invalid_tool_calls_are_dropped_before_reaching_the_page():
    assert server.check_args("show_pie", {}) == ["unknown tool show_pie"]
    assert server.check_args("show_metric", {"label": "x"}) == ["show_metric: missing value"]


def test_input_is_validated_with_the_official_schema():
    inp = RunAgentInput.model_validate(agui_input("hi"))
    assert inp.messages[0].role == "user"


def test_prompt_contains_the_data_and_tools_are_offered():
    server.llm.calls.clear()
    events()
    call = server.llm.calls[-1]
    assert "Campus Coffee Cart" in call["messages"][0]["content"]
    assert {t["name"] for t in call["tools"]} == server.TOOL_NAMES
