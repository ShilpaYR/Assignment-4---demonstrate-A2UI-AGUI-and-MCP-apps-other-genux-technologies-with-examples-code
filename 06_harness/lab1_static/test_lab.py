"""Offline tests for harness lab 1 (static)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import agui_input, post_sse, start  # noqa: E402
from harness import Workspace  # noqa: E402
from surfaces import TerminalSurface  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def test_loop_reads_files_then_calls_ui_tools_then_answers():
    events = []
    h = agent.build_harness().on(lambda kind, d: events.append((kind, d.get("name") or d.get("tool"))))
    final = h.run("dashboard")
    calls = [n for k, n in events if k == "tool_call"]
    assert calls[:3] == ["list_files", "read_file", "read_file"] and calls.count("show_metric") == 3
    assert [n for k, n in events if k == "ui"] == ["show_metric"] * 3 + ["show_chart", "show_table"]
    assert final.startswith("Revenue was $4,669.20")


def test_tool_results_go_back_to_the_model():
    h = agent.build_harness()
    h.run("dashboard")
    tool_msgs = [m for m in h.messages if m["role"] == "tool"]
    assert "Mon,182,655.20" in tool_msgs[1]["content"]   # read_file result is in the conversation


def test_workspace_is_a_sandbox():
    ws = Workspace()
    try:
        ws.path("../../etc/passwd")
        raise AssertionError("escaped the workspace")
    except PermissionError:
        pass


def test_terminal_surface_draws_ui_tools():
    term = TerminalSurface()
    agent.build_harness().on(term).run("dashboard")
    assert "$4,669.20" in term.text() and "Oat latte" in term.text()


def test_web_surface_bridges_the_run_to_agui():
    events = post_sse(f"{start(build_web(agent.build_harness(), title='t', mode='static', prompt='p'))}/agui", agui_input("p"))
    assert events[0]["type"] == "RUN_STARTED" and events[-1]["type"] == "RUN_FINISHED"
    assert sum(e["type"] == "TOOL_CALL_RESULT" for e in events) == 8
