"""Recorded demo for A2UI lab 1 (static): developer template + agent data, then a click."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402  (server put shared/ on sys.path)


def main():
    banner("Part 2 / Lab 2.1 - A2UI static: developer-written surface, agent-written data")
    url = start(server.build_app())
    msgs = post_sse(f"{url}/a2ui/stream", {})
    comps = msgs[0]["createSurface"]["components"]
    print(f"createSurface: {len(comps)} components from the developer template, e.g.")
    for c in comps[5:7] + comps[12:14]:
        print("   ", compact(c, 110))
    for m in msgs[1:]:
        print("updateDataModel", m["updateDataModel"]["path"], "=", compact(m["updateDataModel"]["value"], 80))
    print("official schema check (jsonschema):", a2ui.validate_stream(msgs) or "valid")
    res = a2ui.official_check(msgs)
    print("official renderer core (@a2ui/web_core):", "skipped (run npm install)" if res is None else ("accepted" if res["ok"] else res["errors"]))
    action = {"version": "1.0", "action": {"name": "restock_beans", "surfaceId": "coffee_dashboard", "sourceComponentId": "restock_btn",
              "timestamp": a2ui.now(), "context": {"kg": 10, "beansNow": 3.5}}}
    print("POST /a2ui/action", compact(action["action"], 100))
    for r in json.loads(post(f"{url}/a2ui/action", action)):
        print("   <-", compact(r, 110))
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=Oat latte")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=Ordered 10 kg")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
