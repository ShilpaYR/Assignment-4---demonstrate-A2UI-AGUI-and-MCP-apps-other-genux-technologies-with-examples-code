"""Offline tests for MCP Apps lab 3 (open-ended)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.sandbox import check_html  # noqa: E402
from host import McpConnection  # noqa: E402
from mcpapps import official_check  # noqa: E402

CONN = McpConnection(HERE / "server.py")


def test_widget_html_is_generated_server_side_and_passes_policy():
    r = CONN.call("generate_widget", {"request": "calculator"})
    assert not r["isError"] and check_html(r["structuredContent"]["html"]) == []
    assert r["structuredContent"]["allowedEvents"] == ["apply_price"]


def test_view_mounts_the_widget_in_its_own_sandbox():
    html = CONN.resource("ui://coffee/widget-host.html")["text"]
    assert "mountSandboxed" in html and 'sandbox", "allow-scripts"' in html


def test_recorded_bridge_traffic_matches_the_official_schemas():
    log_file = HERE / "bridge_log.json"
    if not log_file.exists():
        pytest.skip("run demo.py first")
    log = json.loads(log_file.read_text())
    assert any(e["msg"].get("method") == "ui/update-model-context" for e in log)
    res = official_check(log)
    if res is None:
        pytest.skip("node / @modelcontextprotocol/ext-apps not installed")
    assert res["ok"], res["errors"]
