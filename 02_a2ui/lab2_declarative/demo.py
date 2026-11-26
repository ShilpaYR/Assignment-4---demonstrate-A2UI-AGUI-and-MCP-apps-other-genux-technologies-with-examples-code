"""Recorded demo for A2UI lab 2 (declarative): correction loop, batched surface, two-way binding."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, post, snap, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def main():
    banner("Part 2 / Lab 2.2 - A2UI declarative: the model writes the surface")
    print("system prompt (generated from the official basic catalog), first lines:")
    for line in server.SYSTEM.splitlines()[:5]:
        print("  | " + line[:100])
    url = start(server.build_app())
    raw = post(f"{url}/a2ui/stream", {"prompt": "dashboard + order form"})
    events = read_sse(raw)
    for e in events:
        if "attempt" in e:
            print(f"attempt {e['attempt']}: {'VALID' if e['valid'] else 'INVALID'}")
            for err in e["errors"]:
                print("   -", err[:118])
    msgs = [e for e in events if "version" in e]
    print("streamed:", ", ".join(f"{a2ui.message_kind(m)}({len(m['updateComponents']['components'])})" if "updateComponents" in m
                                 else a2ui.message_kind(m) for m in msgs))
    res = a2ui.official_check(msgs)
    print("official renderer core (@a2ui/web_core):", "skipped" if res is None else ("accepted" if res["ok"] else res["errors"]))
    act = {"version": "1.0", "action": {"name": "submit_order", "surfaceId": "coffee_dashboard", "sourceComponentId": "order_btn",
           "timestamp": a2ui.now(), "context": {"kg": 12, "note": "medium roast", "express": True}}}
    print("action  ->", compact(act["action"]["context"]), "<-", compact(json.loads(post(f"{url}/a2ui/action", act))[0]["updateDataModel"]))
    with browser_page(height=1100) as page:
        if page:
            page.goto(url)
            page.wait_for_selector(".g-skeleton")
            snap(page, HERE, "screenshot_partial.png")
            page.wait_for_selector("text=done:")
            page.fill("[data-bind='/order/note']", "medium roast")
            page.check("[data-bind='/order/express']")
            page.click("[data-action=submit_order]")
            page.wait_for_selector("text=Order #1042")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
