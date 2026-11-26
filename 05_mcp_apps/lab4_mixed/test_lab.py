"""Offline tests for MCP Apps lab 4 (mixed)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.catalog import validate_spec  # noqa: E402
from host import McpConnection, visibility  # noqa: E402
from mcpapps import official_check  # noqa: E402
import text_host  # noqa: E402

CONN = McpConnection(HERE / "server.py")


def test_hybrid_spec_is_valid_with_one_generated_view():
    spec = CONN.call("coffee_dashboard_hybrid", {})["structuredContent"]["spec"]
    assert validate_spec(spec, hybrid=True, actions={"restock_beans"}) == []
    assert [el["type"] for el in spec["elements"].values()].count("GeneratedView") == 1


def test_interaction_tools_are_app_only_and_validate_input():
    tools = {t["name"]: t for t in CONN.tools()}
    assert visibility(tools["apply_price"]) == ["app"] and visibility(tools["restock_beans"]) == ["app"]
    assert CONN.call("apply_price", {"price": 40})["isError"]
    assert CONN.call("apply_price", {"price": 4})["structuredContent"]["ops"][0]["value"] == "$4.00"


def test_text_only_host_still_gets_a_useful_answer():
    out = text_host.run(HERE / "server.py", "coffee_dashboard_hybrid", {})
    assert "Revenue $4,669.20" in out and "apply_price" not in out.splitlines()[0]


def test_recorded_bridge_traffic_matches_the_official_schemas():
    log_file = HERE / "bridge_log.json"
    if not log_file.exists():
        pytest.skip("run demo.py first")
    res = official_check(json.loads(log_file.read_text()))
    if res is None:
        pytest.skip("node / @modelcontextprotocol/ext-apps not installed")
    assert res["ok"], res["errors"]
