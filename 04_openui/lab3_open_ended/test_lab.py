"""Offline tests for OpenUI lab 3 (open-ended)."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import post, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import oui  # noqa: E402


def events():
    return read_sse(post(f"{start(server.build_app())}/oui/stream", {}))


def test_answer_is_one_artifact_and_passes_parser_and_policy():
    summary = events()[-1]
    assert summary["errors"] == [] and summary["statements"] == 2


def test_artifact_is_partial_until_the_string_closes():
    program = "".join(e.get("delta", "") for e in events())
    half = oui.official_parse(program[: len(program) // 2], "html")
    if half is None:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert half["root"]["props"]["children"][0]["partial"] is True


def test_policy_runs_on_the_artifact_document(tmp_path, monkeypatch):
    from common.llm import ScriptedLLM
    (tmp_path / "calculator.oui").write_text('root = Stack([c])\nc = HtmlArtifact("x", "<script>fetch(1)</script>")\n')
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    if oui.official_parse("root = Stack([])\n", "html") is None:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert "HtmlArtifact: network APIs are not allowed" in events()[-1]["errors"]


def test_artifact_events_are_validated():
    assert "4.60" in server.handle_action({"action": "apply_price", "params": {"price": 4.6}})["message"]
    assert "error" in server.handle_action({"action": "apply_price", "params": {"price": "<script>"}})
