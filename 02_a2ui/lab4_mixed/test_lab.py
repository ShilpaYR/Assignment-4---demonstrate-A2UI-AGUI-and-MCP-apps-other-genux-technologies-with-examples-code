"""Offline tests for A2UI lab 4 (mixed)."""
import json
import sys
from pathlib import Path

import pytest

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def act(name, source, ctx):
    return {"version": "1.0", "action": {"name": name, "surfaceId": "s", "sourceComponentId": source,
            "timestamp": "2026-11-24T10:00:00Z", "context": ctx}}


def components():
    return [c for m in server.generate("x") for c in (m.get("updateComponents") or {}).get("components", [])]


def test_one_htmlframe_from_the_custom_catalog_rest_from_basic():
    comps = components()
    frames = [c for c in comps if c["component"] == "HtmlFrame"]
    assert len(frames) == 1 and frames[0]["@catalogId"] == a2ui.HTML_CATALOG_ID
    assert all("@catalogId" not in c for c in comps if c["component"] != "HtmlFrame")


def test_official_core_accepts_the_mixed_surface():
    res = a2ui.official_check(server.generate("x"))
    if res is None:
        pytest.skip("node / @a2ui/web_core not installed")
    assert res["ok"], res["errors"]


def test_htmlframe_without_catalog_id_is_rejected(tmp_path, monkeypatch):
    text = (HERE / "fixtures" / "dashboard_mixed.jsonl").read_text().replace('"@catalogId":"https://catalogs.genux.example/html/v1/catalog.json",', "")
    (tmp_path / "dashboard_mixed.jsonl").write_text(text)
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    with pytest.raises(ValueError):
        server.generate("x")


def test_all_four_message_types_are_used():
    kinds = {a2ui.message_kind(m) for m in server.generate("x")}
    kinds |= {a2ui.message_kind(m) for m in server.handle_action(act("restock_beans", "restock_btn", {"kg": 10, "beansNow": 3.5}))}
    kinds |= {a2ui.message_kind(m) for m in server.handle_action(act("close_surface", "close_btn", {}))}
    assert kinds == {"createSurface", "updateComponents", "updateDataModel", "deleteSurface"}


def test_price_event_only_accepted_from_the_frame():
    assert "ticket" in json.dumps(server.handle_action(act("apply_price", "whatif", {"price": 4.1})))
    assert "error" in server.handle_action(act("apply_price", "restock_btn", {"price": 4.1}))[0]
