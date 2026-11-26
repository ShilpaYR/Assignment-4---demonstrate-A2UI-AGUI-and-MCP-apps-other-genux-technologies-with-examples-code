"""Offline tests for OpenUI lab 2 (declarative)."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import post, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import oui  # noqa: E402


def program():
    return "".join(e.get("delta", "") for e in read_sse(post(f"{start(server.build_app())}/oui/stream", {})))


def test_program_parses_with_the_official_parser():
    res = oui.official_parse(program(), "declarative")
    if res is None:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert res["ok"] and res["elements"] == 11


def test_forward_references_are_unresolved_then_resolved():
    lines = program().splitlines()
    early = oui.official_parse("\n".join(lines[:2]) + "\n", "declarative")
    if early is None:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert set(early["meta"]["unresolved"]) == {"kpis", "chart", "items", "stock"}


def test_unknown_component_is_reported():
    assert "PieChart" in oui.check('root = Stack([p])\np = PieChart([1, 2])\n', "declarative")[0]


def test_edit_is_a_single_replacement_statement():
    patch = server.handle_action({"action": "restock_beans"})["patch"]
    assert oui.statements(patch) == [("beans", 'Text("Beans on hand: 13.5 kg - 10 kg ordered.", "strong")')]
