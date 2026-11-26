"""Offline tests for harness lab 2 (declarative)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import agui_input, post_sse, start  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def test_invalid_spec_is_a_tool_error_with_actionable_messages():
    out = agent.render_ui({"root": "a", "elements": {"a": {"type": "PieChart", "props": {}, "children": []}}})
    assert "unknown component 'PieChart'" in out["error"]


def test_the_loop_retries_and_the_second_spec_is_shown():
    events = []
    agent.build_harness().on(lambda k, d: events.append((k, d))).run("dashboard")
    renders = [d for k, d in events if k == "tool_result" and d["name"] == "render_ui"]
    assert [r["ok"] for r in renders] == [False, True]
    assert sum(1 for k, _ in events if k == "ui") == 1           # only the valid spec reached the surfaces


def test_only_the_valid_spec_reaches_the_web_page():
    events = post_sse(f"{start(build_web(agent.build_harness(), title='t', mode='declarative', prompt='p'))}/agui", agui_input("p"))
    snaps = [e for e in events if e["type"] == "STATE_SNAPSHOT"]
    assert len(snaps) == 1 and "pie" not in snaps[0]["snapshot"]["ui"]["elements"]
