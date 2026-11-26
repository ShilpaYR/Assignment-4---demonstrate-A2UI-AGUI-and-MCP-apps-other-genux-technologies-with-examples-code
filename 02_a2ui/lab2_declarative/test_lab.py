"""Offline tests for A2UI lab 2 (declarative)."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def run():
    return list(server.generate("x"))


def test_first_attempt_is_rejected_with_readable_errors():
    first = run()[0][1]
    assert not first["valid"]
    assert any("'h2' is not one of ['caption', 'body']" in e for e in first["errors"])
    assert any('"@path"' in e for e in first["errors"])


def test_errors_are_fed_back_to_the_model():
    server.llm.calls.clear()
    run()
    assert "failed validation" in server.llm.calls[1]["user"] and "'h2'" in server.llm.calls[1]["user"]


def test_second_attempt_is_valid_and_official_core_agrees():
    kind, msgs = run()[-1]
    assert kind == "messages" and a2ui.validate_stream(msgs) == []
    res = a2ui.official_check(msgs)
    if res is None:
        pytest.skip("node / @a2ui/web_core not installed")
    assert res["ok"], res["errors"]


def test_gives_up_after_three_invalid_attempts(tmp_path, monkeypatch):
    for i in (1, 2, 3):
        (tmp_path / f"attempt{i}.jsonl").write_text('{"version": "1.0", "createSurface": {}}\n')
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    with pytest.raises(RuntimeError):
        run()


def test_components_stream_in_batches_root_first():
    msgs = list(server.batches(run()[-1][1]))
    updates = [m for m in msgs if "updateComponents" in m]
    assert len(updates) >= 3 and updates[0]["updateComponents"]["components"][0]["id"] == "root"


def test_order_action_validates_bound_values():
    def act(ctx):
        return {"version": "1.0", "action": {"name": "submit_order", "surfaceId": "s", "sourceComponentId": "order_btn",
                "timestamp": "2026-11-24T10:00:00Z", "context": ctx}}
    ok = server.handle_action(act({"kg": 12, "express": True, "note": ""}))[0]["updateDataModel"]["value"]
    bad = server.handle_action(act({"kg": 500}))[0]["updateDataModel"]["value"]
    assert ok == "Order #1042 confirmed: 12 kg express." and "between 1 and 50" in bad
