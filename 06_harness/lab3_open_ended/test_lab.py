"""Offline tests for harness lab 3 (open-ended)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import agui_input, post_sse, start  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def test_render_html_saves_an_artifact_with_csp_first():
    out = agent.render_html("Test widget", "<html><head><title>t</title></head><body>ok</body></html>")
    saved_file = HERE / out["path"]
    saved = saved_file.read_text()
    saved_file.unlink()
    assert saved.index("Content-Security-Policy") < saved.index("<title>")


def test_policy_violations_are_tool_errors():
    assert "network APIs" in agent.render_html("x", "<script>fetch('/x')</script>")["error"]


def test_web_surface_receives_the_document_as_an_activity():
    events = post_sse(f"{start(build_web(agent.build_harness(), title='t', mode='open-ended', prompt='p'))}/agui", agui_input("p"))
    act = next(e for e in events if e["type"] == "ACTIVITY_SNAPSHOT")
    assert act["activityType"] == "genux.sandboxed_html" and "genux.emit" in act["content"]["html"]
