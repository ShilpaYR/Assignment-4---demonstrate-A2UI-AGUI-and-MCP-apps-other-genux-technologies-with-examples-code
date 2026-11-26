"""Offline tests for json-render lab 3 (open-ended)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def test_one_htmlblock_with_a_state_caption_and_an_event_binding():
    spec = jr.apply_stream("\n".join(json.dumps(o) for o in server.patches("x")))
    (el,) = spec["elements"].values()
    assert el["type"] == "HtmlBlock" and el["props"]["caption"] == {"$state": "/status"}
    assert el["on"] == {"apply_price": {"action": "apply_price"}}


def test_html_catalog_rejects_other_components():
    spec = {"root": "a", "elements": {"a": {"type": "Metric", "props": {"label": "x", "value": "1"}, "children": []}}}
    assert "unknown component 'Metric'" in jr.validate(spec, "html")[0]


def test_official_library_accepts_the_stream():
    res = jr.official_check("\n".join(json.dumps(o) for o in server.patches("x")), "html", stream=True)
    if res is None:
        pytest.skip("node / @json-render/core not installed")
    assert res["ok"], res["issues"]


def test_network_html_is_refused(tmp_path, monkeypatch):
    bad = {"op": "add", "path": "/elements/w", "value": {"type": "HtmlBlock", "props": {"title": "t", "html": "<img src='https://x.example/t.png'>", "caption": None}, "children": []}}
    (tmp_path / "widget.jsonl").write_text('{"op":"add","path":"/root","value":"w"}\n' + json.dumps(bad) + "\n")
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    with pytest.raises(ValueError, match="remote resources"):
        server.patches("x")


def test_action_validation():
    assert "3.80" in server.handle_action({"action": "apply_price", "params": {"price": 3.8}})[0]["value"]
    assert "Ignored" in server.handle_action({"action": "apply_price", "params": {"price": 99}})[0]["value"]
