"""Offline tests for A2UI lab 1 (static)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import post_sse, start  # noqa: E402
from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def stream():
    return post_sse(f"{start(server.build_app())}/a2ui/stream", {})


def test_structure_first_then_only_data():
    msgs = stream()
    assert a2ui.message_kind(msgs[0]) == "createSurface" and msgs[0]["createSurface"]["components"] == server.TEMPLATE
    assert {a2ui.message_kind(m) for m in msgs[1:]} == {"updateDataModel"}


def test_every_message_passes_the_official_schema():
    assert a2ui.validate_stream(stream()) == []


def test_official_renderer_core_accepts_the_stream():
    res = a2ui.official_check(stream())
    if res is None:
        pytest.skip("node / @a2ui/web_core not installed")
    assert res["ok"], res["errors"]
    assert res["surfaces"]["coffee_dashboard"]["kpis"]["revenue"] == "$4,669.20"


def test_bad_tool_arguments_never_reach_the_page(tmp_path, monkeypatch):
    (tmp_path / "fill_dashboard.json").write_text(json.dumps([{"tool_calls": [{"name": "fill_dashboard", "arguments": {"kpis": {}}}]}]))
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    with pytest.raises(ValueError):
        server.stream("x")


def test_action_round_trip():
    act = {"version": "1.0", "action": {"name": "restock_beans", "surfaceId": "s", "sourceComponentId": "restock_btn",
           "timestamp": "2026-11-24T10:00:00Z", "context": {"kg": 10, "beansNow": 3.5}}}
    out = server.handle_action(act)
    assert out[0]["updateDataModel"] == {"surfaceId": "s", "path": "/inventory/beans_kg", "value": 13.5}


def test_malformed_action_is_rejected():
    assert "error" in server.handle_action({"version": "1.0", "action": {"name": "x"}})[0]
