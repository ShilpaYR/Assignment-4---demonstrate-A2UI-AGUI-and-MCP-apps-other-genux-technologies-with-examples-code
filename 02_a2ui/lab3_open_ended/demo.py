"""Recorded demo for A2UI lab 3 (open-ended): HtmlFrame from a custom catalog, events as A2UI actions."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import a2ui  # noqa: E402


def main():
    banner("Part 2 / Lab 2.3 - A2UI open-ended: one HtmlFrame from a custom catalog")
    url = start(server.build_app())
    msg = post_sse(f"{url}/a2ui/stream", {})[0]
    frame = msg["createSurface"]["components"][0]
    print("createSurface catalogId:", msg["createSurface"]["catalogId"])
    print("component:", compact({k: (v if k != "html" else f"<{len(v)} chars of HTML>") for k, v in frame.items()}, 160))
    print("validate against basic catalog only :", a2ui.validate_message(msg)[0][:90])
    print("validate with the custom catalog    :", a2ui.validate_message(msg, with_html=True) or "valid")
    res = a2ui.official_check([msg])
    print("official renderer core (@a2ui/web_core) + custom catalog:", "skipped" if res is None else ("accepted" if res["ok"] else res["errors"]))
    with browser_page() as page:
        if page:
            page.goto(url)
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("4.5")
            f.click("#apply")
            page.wait_for_selector("text=Agent received price")
            print("browser: iframe event ->", page.locator(".wire .entry").nth(1).inner_text()[:110])
            print("         A2UI action  ->", page.locator(".wire .entry").nth(2).inner_text()[:110])
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
