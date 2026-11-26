"""Recorded demo for A2UI lab 4 (mixed): two catalogs on one surface, all four message types."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def act(name, source, ctx):
    return {"version": "1.0", "action": {"name": name, "surfaceId": "coffee_dashboard", "sourceComponentId": source,
            "timestamp": a2ui.now(), "context": ctx}}


def main():
    banner("Part 2 / Lab 2.4 - A2UI mixed: basic catalog + one HtmlFrame on one surface")
    url = start(server.build_app())
    msgs = post_sse(f"{url}/a2ui/stream", {})
    comps = [c for m in msgs for c in (m.get("updateComponents") or {}).get("components", [])]
    by_catalog = {}
    for c in comps:
        by_catalog.setdefault(c.get("@catalogId", "(surface default: basic)"), []).append(c["component"])
    for cat, names in by_catalog.items():
        print(f"{cat}: {len(names)} components ({', '.join(sorted(set(names)))})")
    res = a2ui.official_check(msgs)
    print("official renderer core (@a2ui/web_core):", "skipped" if res is None else ("accepted" if res["ok"] else res["errors"]))
    for a in (act("restock_beans", "restock_btn", {"kg": 10, "beansNow": 3.5}), act("apply_price", "whatif", {"price": 4.1}),
              act("close_surface", "close_btn", {})):
        replies = json.loads(post(f"{url}/a2ui/action", a))
        print(f"action {a['action']['name']:<14}->", ", ".join(a2ui.message_kind(r) for r in replies))
        for r in replies[:2]:
            print("     ", compact(r, 116))
    with browser_page(height=1100) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=basic-catalog components")
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("4.1")
            f.click("#apply")
            page.wait_for_selector("text=updated to $4.10")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=Receipt")
            print("after restock the frame kept its slider at:", inner_frame(page).locator("#priceOut").inner_text())
            snap(page, HERE, "screenshot.png")
            page.click("[data-action=close_surface]")
            page.wait_for_selector("[data-surface]", state="detached")
            print("close_surface -> deleteSurface: surface removed from the page")


if __name__ == "__main__":
    main()
