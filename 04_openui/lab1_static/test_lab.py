"""Offline tests for OpenUI lab 1 (static)."""
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


def test_library_offers_only_prebuilt_components():
    assert oui.components("static") == {"Stack", "SalesDashboard", "InventoryCard"}
    assert "SalesDashboard(title: string" in server.SYSTEM


def test_program_uses_only_prebuilt_components_and_parses():
    text = program()
    assert oui.quick_check(text, "static") == []
    res = oui.official_parse(text, "static")
    if res is None:
        pytest.skip("node / @openuidev/lang-core not installed")
    assert res["ok"] and res["elements"] == 3


def test_a_primitive_is_rejected_in_the_static_library():
    assert "unknown component Metric" in oui.quick_check('root = Stack([m])\nm = Metric("a", "b")\n', "static")[0]


def test_action_answers_with_an_edit_statement():
    assert server.handle_action({"action": "restock_beans"})["patch"] == "stock = InventoryCard(13.5, 5.0)\n"
    assert "error" in server.handle_action({"action": "drop"})
