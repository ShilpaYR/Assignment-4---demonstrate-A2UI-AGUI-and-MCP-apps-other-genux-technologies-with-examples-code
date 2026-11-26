"""Recorded demo for json-render lab 4 (mixed): hybrid spec, actions, and the terminal renderer."""
import json
import sys
import urllib.request
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def main():
    banner("Part 3 / Lab 3.4 - json-render mixed: hybrid catalog, one spec, two renderers")
    url = start(server.build_app())
    ops = post_sse(f"{url}/jr/stream", {})
    types = [o["value"]["type"] for o in ops if o["path"].startswith("/elements/")]
    print(f"{len(ops)} patches: {len(types)} elements ({', '.join(sorted(set(types)))}) + {sum(o['path'].startswith('/state') for o in ops)} state patches")
    res = jr.official_check("\n".join(json.dumps(o) for o in ops), "hybrid", stream=True)
    print("official compileSpecStream + hybridCatalog props:", "skipped" if res is None else (res["issues"] or "valid"))
    state = jr.apply_stream("\n".join(json.dumps(o) for o in ops))["state"]
    for body in ({"action": "restock_beans", "params": {"kg": 10}, "state": state},
                 {"action": "apply_price", "params": {"price": 4.25}},
                 {"action": "apply_price", "params": {"price": 400}}):
        print(f"action {body['action']} {body['params']} ->", compact(json.loads(post(f"{url}/jr/action", body)), 120))
    print("--- the same spec, second renderer (rich, terminal):")
    text = urllib.request.urlopen(f"{url}/jr/terminal").read().decode()
    lines = text.rstrip().splitlines()
    print("\n".join(lines[:16] + ["   ..."] + lines[-6:]))
    with browser_page(height=1000) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=custom actions go to the server")
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("4.25")
            f.click("#apply")
            page.wait_for_selector("text=Avg ticket set to $4.25")
            page.click("text=Hide top items")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=order placed")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
