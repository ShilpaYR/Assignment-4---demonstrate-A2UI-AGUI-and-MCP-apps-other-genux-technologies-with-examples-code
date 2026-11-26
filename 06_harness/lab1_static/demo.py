"""Recorded demo for harness lab 1 (static): one agent run, two surfaces."""
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common import scenario  # noqa: E402
from common.demo import agui_input, banner, browser_page, post_sse, snap, start  # noqa: E402
from surfaces import TerminalSurface  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def main():
    banner("Part 6 / Lab 6.1 - harness static: UI tools next to file tools, two surfaces")
    term = TerminalSurface(width=90)
    agent.build_harness().on(term).run(scenario.DASHBOARD_PROMPT)
    lines = term.text().rstrip().splitlines()
    print("--- surface 1: terminal")
    print("\n".join(lines[:14] + ["   ... (chart and table panels) ..."] + lines[-1:]))
    url = start(build_web(agent.build_harness(), title="Lab 1 - UI tools in the agent loop", mode="static", prompt=scenario.DASHBOARD_PROMPT))
    events = post_sse(f"{url}/agui", agui_input(scenario.DASHBOARD_PROMPT))
    print("--- surface 2: the same run bridged to AG-UI")
    print("events:", dict(Counter(e["type"] for e in events)))
    print("tool calls in order:", [e["toolCallName"] for e in events if e["type"] == "TOOL_CALL_START"])
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=run finished")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
