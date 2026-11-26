"""Offline tests for AG-UI lab 2 (declarative)."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, post_sse, start  # noqa: E402
from common.jsonpatch import apply  # noqa: E402
from common.llm import ScriptedLLM  # noqa: E402
import server  # noqa: E402


def run_events():
    return post_sse(f"{start(server.build_app())}/agui", agui_input("dashboard"))


def test_deltas_rebuild_exactly_the_generated_spec():
    events = run_events()
    state = {}
    for e in events:
        if e["type"] == "STATE_SNAPSHOT":
            state = e["snapshot"]
        elif e["type"] == "STATE_DELTA":
            state = apply(state, e["delta"])
    expected = json.loads((HERE / "fixtures" / "dashboard_spec.json").read_text())
    assert state["ui"] == expected


def test_parent_arrives_before_children():
    paths = [e["delta"][0]["path"] for e in run_events() if e["type"] == "STATE_DELTA"]
    assert paths[0] == "/ui/root" and paths[1] == "/ui/elements/dash"
    assert paths.index("/ui/elements/kpis") < paths.index("/ui/elements/m-rev")


def test_pipeline_steps_are_reported():
    steps = [e["stepName"] for e in run_events() if e["type"] == "STEP_STARTED"]
    assert steps == ["generate", "validate", "publish"]


def test_invalid_layout_becomes_run_error(tmp_path, monkeypatch):
    bad = {"root": "x", "elements": {"x": {"type": "PieChart", "props": {}, "children": []}}}
    (tmp_path / "dashboard_spec.json").write_text(json.dumps(bad))
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    events = run_events()
    assert events[-1]["type"] == "RUN_ERROR" and "unknown component 'PieChart'" in events[-1]["message"]
    assert not any(e["type"] == "STATE_DELTA" for e in events)


def test_prompt_is_generated_from_the_catalog():
    for name in ("Card", "Metric", "BarChart", "Table"):
        assert f"- {name}(" in server.SYSTEM
