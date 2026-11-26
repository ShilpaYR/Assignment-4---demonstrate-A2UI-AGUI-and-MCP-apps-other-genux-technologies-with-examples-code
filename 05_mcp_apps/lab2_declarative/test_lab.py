"""Offline tests for MCP Apps lab 2 (declarative)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.catalog import validate_spec  # noqa: E402
from host import McpConnection  # noqa: E402
from mcpapps import official_check  # noqa: E402

CONN = McpConnection(HERE / "server.py")


def test_tool_returns_a_valid_catalog_spec():
    r = CONN.call("render_dashboard", {"request": "dashboard"})
    assert not r["isError"] and validate_spec(r["structuredContent"]["spec"], actions={"restock_beans"}) == []


def test_ui_action_returns_patches_and_rejects_unknown_actions():
    ok = CONN.call("ui_action", {"action": "restock_beans", "params": {"kg": 10}})
    assert ok["structuredContent"]["ops"][0]["path"] == "/elements/note/props/text"
    assert CONN.call("ui_action", {"action": "format_disk"})["isError"]


def test_view_is_generic_it_contains_no_dashboard_data():
    html = CONN.resource("ui://coffee/catalog-view.html")["text"]
    assert "renderSpec" in html and "$4,669.20" not in html


def test_recorded_bridge_traffic_matches_the_official_schemas():
    log_file = HERE / "bridge_log.json"
    if not log_file.exists():
        pytest.skip("run demo.py first")
    res = official_check(json.loads(log_file.read_text()))
    if res is None:
        pytest.skip("node / @modelcontextprotocol/ext-apps not installed")
    assert res["ok"], res["errors"]
