"""Offline tests for json-render lab 2 (declarative)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def run():
    return list(server.stream("x"))


def test_the_prompt_is_the_librarys_own():
    assert "OUTPUT FORMAT (JSONL, RFC 6902 JSON Patch)" in server.SYSTEM and "- Metric:" in server.SYSTEM


def test_hallucinated_component_is_dropped_the_rest_streams():
    out = run()
    rejected = [v for k, v in out if k == "meta" and not v.get("done")]
    assert rejected[0]["rejected"] == "/elements/pie" and "unknown component 'PieChart'" in rejected[0]["errors"][0]
    summary = out[-1][1]
    assert summary["elements"] == 10 and summary["issues"] == []


def test_patches_arrive_parent_first():
    paths = [v["path"] for k, v in run() if k == "op"]
    assert paths[:2] == ["/root", "/elements/dash"]


def test_python_and_official_compile_agree():
    accepted = "\n".join(json.dumps(v) for k, v in run() if k == "op")
    res = jr.official_check(accepted, "base", stream=True)
    if res is None:
        pytest.skip("node / @json-render/core not installed")
    assert res["ok"] and res["spec"] == jr.apply_stream(accepted)


def test_a_line_that_is_not_json_is_reported(tmp_path, monkeypatch):
    (tmp_path / "dashboard.jsonl").write_text('{"op":"add","path":"/root","value":"a"}\nnot json at all\n')
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    metas = [v for k, v in run() if k == "meta"]
    assert metas[0]["rejected"].startswith("not json")


def test_last_line_without_newline_is_not_lost():
    assert list(server.lines(["a\nb", "c"])) == ["a", "bc"]
