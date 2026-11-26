"""Offline tests for MCP Apps lab 1 (static). The MCP server runs for real, over stdio."""
import json
import re
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from host import McpConnection, visibility  # noqa: E402
from mcpapps import official_check  # noqa: E402

CONN = McpConnection(HERE / "server.py")


def tools():
    return {t["name"]: t for t in CONN.tools()}


def test_tool_points_at_a_ui_resource_and_app_only_tool_is_hidden_from_the_model():
    t = tools()
    assert t["coffee_dashboard"]["_meta"]["ui"]["resourceUri"] == "ui://coffee/dashboard.html"
    assert visibility(t["restock_beans"]) == ["app"]


def test_resource_is_a_self_contained_mcp_app_document():
    res = CONN.resource("ui://coffee/dashboard.html")
    assert res["mimeType"] == "text/html;profile=mcp-app"
    assert res["_meta"]["ui"]["csp"] == {"connectDomains": [], "resourceDomains": []}
    assert "McpAppBridge" in res["text"] and not re.search(r"<script[^>]+src=", res["text"])


def test_result_has_text_for_the_model_and_data_for_the_view():
    r = CONN.call("coffee_dashboard", {"days": 3})
    assert r["content"][0]["text"].startswith("Campus Coffee Cart")
    assert r["structuredContent"]["labels"] == ["Fri", "Sat", "Sun"]


def test_recorded_bridge_traffic_matches_the_official_schemas():
    log_file = HERE / "bridge_log.json"
    if not log_file.exists():
        pytest.skip("run demo.py first to record the bridge traffic")
    res = official_check(json.loads(log_file.read_text()))
    if res is None:
        pytest.skip("node / @modelcontextprotocol/ext-apps not installed")
    assert res["ok"] and res["checked"] >= 5, res["errors"]
