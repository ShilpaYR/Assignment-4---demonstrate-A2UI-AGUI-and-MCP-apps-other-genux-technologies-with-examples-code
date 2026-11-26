"""Offline tests for json-render lab 1 (static)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.jsonpatch import apply  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def test_template_values_are_all_state_expressions():
    metric = server.TEMPLATE["elements"]["m-rev"]["props"]
    assert metric["value"] == {"$state": "/kpis/revenue"}


def test_agent_only_patches_state():
    ops = server.patches("x")
    assert ops[0]["path"] == "" and all(op["path"].startswith("/state/") for op in ops[1:])


def test_applied_stream_is_a_valid_spec_with_data():
    spec = apply({}, server.patches("x"))
    assert jr.validate(spec, "base") == [] and spec["state"]["kpis"]["revenue"] == "$4,669.20"


def test_official_library_accepts_the_template():
    res = jr.official_check(json.dumps(server.TEMPLATE), "base")
    if res is None:
        pytest.skip("node / @json-render/core not installed")
    assert res["ok"], res["issues"]


def test_restock_action_returns_state_patches_and_unknown_actions_are_refused():
    ops = server.handle_action({"action": "restock_beans", "params": {"kg": 10}, "state": {"inventory": {"beans_kg": 3.5}}})
    assert ops[0] == {"op": "replace", "path": "/state/inventory/beans_kg", "value": 13.5}
    assert "error" in server.handle_action({"action": "delete_everything"})[0]
