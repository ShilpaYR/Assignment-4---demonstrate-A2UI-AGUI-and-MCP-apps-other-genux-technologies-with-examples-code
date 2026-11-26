"""Recorded demo for harness lab 2 (declarative): render_ui is validated; the loop self-corrects."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common import scenario  # noqa: E402
from common.demo import agui_input, banner, browser_page, post_sse, snap, start  # noqa: E402
from surfaces import TerminalSurface  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def main():
    banner("Part 6 / Lab 6.2 - harness declarative: render_ui validated, the loop self-corrects")
    term = TerminalSurface(width=96)
    h = agent.build_harness().on(term)
    h.run(scenario.DASHBOARD_PROMPT)
    lines = term.text().rstrip().splitlines()
    print("--- surface 1: terminal")
    print("\n".join(lines[:9] + ["   ... (the dashboard, drawn with rich) ..."] + lines[-1:]))
    errs = [m["content"] for m in h.messages if m["role"] == "tool" and m["content"].startswith('{"error"')]
    print("tool result the model received after attempt 1:")
    for part in json.loads(errs[0])["error"].split("; "):
        print("   ", part[:110])
    url = start(build_web(agent.build_harness(), title="Lab 2 - render_ui with self-correction", mode="declarative", prompt=scenario.DASHBOARD_PROMPT))
    events = post_sse(f"{url}/agui", agui_input(scenario.DASHBOARD_PROMPT))
    print("--- surface 2: AG-UI:", [e["toolCallName"] for e in events if e["type"] == "TOOL_CALL_START"],
          "->", sum(e["type"] == "STATE_SNAPSHOT" for e in events), "STATE_SNAPSHOT (only the valid spec reaches the page)")
    with browser_page(height=1000) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=run finished")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
