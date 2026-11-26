"""Recorded demo for AG-UI lab 1 (static): print the event stream, then screenshot the page."""
import sys
from collections import Counter
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, banner, browser_page, compact, post_sse, snap, start  # noqa: E402
import server  # noqa: E402


def main():
    banner("Part 1 / Lab 1 - AG-UI, static mode: tool calls select pre-built components")
    url = start(server.build_app())
    events = post_sse(f"{url}/agui", agui_input(server.scenario.DASHBOARD_PROMPT))
    print(f"POST /agui -> {len(events)} AG-UI events over SSE")
    for e in events[:9]:
        print("  " + compact(e))
    print("  ...")
    print("  " + compact(events[-1]))
    print("event counts:", dict(Counter(e["type"] for e in events)))
    print("components chosen by the agent:", [e["toolCallName"] for e in events if e["type"] == "TOOL_CALL_START"])
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=run finished")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
