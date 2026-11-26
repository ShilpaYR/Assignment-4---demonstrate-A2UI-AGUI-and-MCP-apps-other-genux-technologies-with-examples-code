"""Offline tests for A2UI lab 3 (open-ended)."""
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def test_surface_uses_the_custom_catalog():
    msg = server.surface_messages("x")[0]
    assert msg["createSurface"]["catalogId"] == a2ui.HTML_CATALOG_ID
    assert msg["createSurface"]["components"][0]["component"] == "HtmlFrame"


def test_basic_catalog_alone_rejects_htmlframe_custom_catalog_accepts():
    msg = server.surface_messages("x")[0]
    assert a2ui.validate_message(msg) and not a2ui.validate_message(msg, with_html=True)


def test_official_core_accepts_with_custom_catalog_registered():
    res = a2ui.official_check(server.surface_messages("x"))
    if res is None:
        pytest.skip("node / @a2ui/web_core not installed")
    assert res["ok"], res["errors"]


def test_policy_blocks_network_html(tmp_path, monkeypatch):
    (tmp_path / "break_even.html").write_text("<script>fetch('https://x.example')</script>")
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    with pytest.raises(ValueError, match="network APIs"):
        server.surface_messages("x")


def test_frame_event_is_a_standard_a2ui_action():
    act = {"version": "1.0", "action": {"name": "apply_price", "surfaceId": "break_even", "sourceComponentId": "root",
           "timestamp": "2026-11-24T10:00:00Z", "context": {"price": 4.5, "breakEvenCups": "277"}}}
    assert a2ui.validate_action(act) == []
    assert "4.50" in server.handle_action(act)[0]["updateDataModel"]["value"]
    act["action"]["context"]["price"] = "free"
    assert "Ignored" in server.handle_action(act)[0]["updateDataModel"]["value"]
