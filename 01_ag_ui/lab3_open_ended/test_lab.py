"""Offline tests for AG-UI lab 3 (open-ended)."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, post_sse, start  # noqa: E402
from common.llm import ScriptedLLM  # noqa: E402
from common.sandbox import check_html, with_csp  # noqa: E402
import server  # noqa: E402


def run_events():
    return post_sse(f"{start(server.build_app())}/agui", agui_input("calculator"))


def test_html_streams_as_text_then_arrives_as_activity():
    events = run_events()
    html = "".join(e["delta"] for e in events if e["type"] == "TEXT_MESSAGE_CONTENT")
    act = next(e for e in events if e["type"] == "ACTIVITY_SNAPSHOT")
    assert act["activityType"] == "genux.sandboxed_html"
    assert act["content"]["status"] == "ready" and act["content"]["html"] == html.strip()
    assert act["content"]["allowedEvents"] == ["apply_price"]


def test_policy_rejects_network_access(tmp_path, monkeypatch):
    (tmp_path / "break_even.html").write_text('<script src="https://evil.example/x.js"></script><script>fetch("/steal")</script>')
    monkeypatch.setattr(server, "llm", ScriptedLLM(tmp_path))
    act = next(e for e in run_events() if e["type"] == "ACTIVITY_SNAPSHOT")["content"]
    assert act["status"] == "rejected" and act["html"] == ""
    assert "external <script src> is not allowed" in act["problems"]
    assert "network APIs are not allowed" in act["problems"]


def test_csp_goes_first_in_head():
    out = with_csp("<html><head><title>x</title></head><body></body></html>")
    assert out.index("Content-Security-Policy") < out.index("<title>")
    assert "connect-src 'none'" in out


def test_generated_document_passes_policy():
    assert check_html((HERE / "fixtures" / "break_even.html").read_text()) == []
