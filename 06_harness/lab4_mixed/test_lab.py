"""Offline tests for harness lab 4 (mixed)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import agui_input, post, post_sse, start  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def setup():
    h = agent.build_harness()
    url = start(build_web(h, title="t", mode="mixed", prompt="p", actions=agent.UI_EVENTS)) + "/agui"
    return h, url


def test_ui_actions_become_turns_and_the_agent_writes_the_workspace():
    h, url = setup()
    post_sse(url, agui_input("p"))
    events = post_sse(url, agui_input("", messages=[], forwarded={"action": "restock_beans", "params": {"kg": 10}}))
    assert [e["toolCallName"] for e in events if e["type"] == "TOOL_CALL_START"] == ["place_order", "update_ui"]
    assert any(m["role"] == "user" and m["content"].startswith("[ui action] restock_beans") for m in h.messages)
    assert json.loads(h.workspace.path("inventory.json").read_text())["beans_kg"] == 13.5


def test_update_ui_revalidates_the_patched_spec():
    h, url = setup()
    post_sse(url, agui_input("p"))
    bad = h.ui_state.update_ui([{"op": "replace", "path": "/elements/chart/props/values", "value": [1]}])
    assert "labels and values differ" in bad["error"]


def test_render_ui_applies_the_html_policy_to_the_generated_view():
    h = agent.build_harness()
    spec = {"root": "g", "elements": {"g": {"type": "GeneratedView", "props": {"title": "x", "html": "<script>fetch(1)</script>"}, "children": []}}}
    assert "network APIs" in h.ui_state.render_ui(spec)["error"]


def test_unknown_page_actions_are_refused():
    _, url = setup()
    assert "not allowed" in post(url, agui_input("", messages=[], forwarded={"action": "rm_rf"}))
