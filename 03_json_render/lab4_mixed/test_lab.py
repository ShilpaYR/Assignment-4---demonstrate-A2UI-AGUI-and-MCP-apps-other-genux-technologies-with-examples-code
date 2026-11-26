"""Offline tests for json-render lab 4 (mixed)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402
import terminal  # noqa: E402


def ops():
    return [e for e in read_sse("".join(server.stream("x"))) if "op" in e]


def test_hybrid_spec_has_catalog_components_and_one_htmlblock():
    types = [o["value"]["type"] for o in ops() if o["path"].startswith("/elements/")]
    assert types.count("HtmlBlock") == 1 and {"Metric", "BarChart", "Table", "Button"} <= set(types)


def test_official_library_accepts_the_hybrid_stream():
    res = jr.official_check("\n".join(json.dumps(o) for o in ops()), "hybrid", stream=True)
    if res is None:
        pytest.skip("node / @json-render/core not installed")
    assert res["ok"], res["issues"]


def test_actions_patch_state_only_and_invalid_ones_are_refused():
    good = server.handle_action({"action": "apply_price", "params": {"price": 4.25}})
    assert all(op["path"].startswith("/state/") for op in good)
    assert "error" in server.handle_action({"action": "apply_price", "params": {"price": 400}})[0]
    assert "error" in server.handle_action({"action": "setState", "params": {}})[0]  # built-ins never reach the server


def test_terminal_renderer_draws_the_same_spec():
    spec = jr.apply_stream("\n".join(json.dumps(o) for o in ops()))
    text = terminal.to_text(spec)
    assert "Campus Coffee Cart" in text and "$4,669.20" in text and "Oat latte" in text
    assert "HtmlBlock" in text and "<script" not in text   # the open-ended region degrades, it never runs
