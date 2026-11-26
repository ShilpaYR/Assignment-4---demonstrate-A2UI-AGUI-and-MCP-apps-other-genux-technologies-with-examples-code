"""Offline tests for OpenUI lab 4 (mixed)."""
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


def test_program_mixes_primitives_and_exactly_one_artifact():
    program = "".join(e.get("delta", "") for e in events())
    kinds = [expr.split("(")[0] for _, expr in oui.statements(program)]
    assert kinds.count("HtmlArtifact") == 1 and {"Metric", "BarChart", "Table", "Button"} <= set(kinds)


def test_parser_and_policy_accept_it_and_the_artifact_dominates_the_budget():
    s = events()[-1]
    if not s["artifact_tokens"]:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert s["errors"] == [] and s["artifact_tokens"] / s["tokens"] > 0.5


def test_events_become_single_statement_edits():
    assert server.handle_action({"action": "apply_price", "params": {"price": 4.2}})["patch"].startswith("ticket = Metric(")
    assert server.handle_action({"action": "restock_beans"})["patch"].startswith("beans = Text(")
    assert "error" in server.handle_action({"action": "apply_price", "params": {"price": 0}})
