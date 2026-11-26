"""Recorded demo for AG-UI lab 2 (declarative): state snapshot + JSON Patch deltas build the UI."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, banner, browser_page, compact, post_sse, snap, start  # noqa: E402
from common.jsonpatch import apply  # noqa: E402
import server  # noqa: E402


def main():
    banner("Part 1 / Lab 2 - AG-UI, declarative mode: the UI is shared state")
    print("system prompt (generated from the catalog), first lines:")
    for line in server.SYSTEM.splitlines()[:6]:
        print("  | " + line[:96])
    url = start(server.build_app())
    events = post_sse(f"{url}/agui", agui_input(server.scenario.DASHBOARD_PROMPT))
    print(f"POST /agui -> {len(events)} events")
    for e in events:
        if e["type"] in ("STEP_STARTED", "STATE_SNAPSHOT") or (e["type"] == "STATE_DELTA" and e["delta"][0]["path"] in ("/ui/root", "/ui/elements/dash", "/ui/elements/kpis")):
            print("  " + compact(e, 120))
    state = {}
    for e in events:
        if e["type"] == "STATE_SNAPSHOT":
            state = e["snapshot"]
        elif e["type"] == "STATE_DELTA":
            state = apply(state, e["delta"])
    deltas = sum(e["type"] == "STATE_DELTA" for e in events)
    print(f"{deltas} STATE_DELTA events rebuilt state.ui with {len(state['ui']['elements'])} elements:",
          ", ".join(f"{k}:{v['type']}" for k, v in state["ui"]["elements"].items()))
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("[data-id=kpis] .g-skeleton, [data-id=kpis] .g-metric")
            snap(page, HERE, "screenshot_partial.png")
            page.wait_for_selector("text=run finished")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
