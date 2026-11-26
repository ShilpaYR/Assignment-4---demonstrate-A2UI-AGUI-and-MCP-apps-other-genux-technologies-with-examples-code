"""Recorded demo for json-render lab 1 (static): template + state patches, local setState, server action."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def main():
    banner("Part 3 / Lab 3.1 - json-render static: developer template + agent state")
    url = start(server.build_app())
    ops = post_sse(f"{url}/jr/stream", {})
    tpl = ops[0]["value"]
    print(f"op 1: replace '' with the template spec ({len(tpl['elements'])} elements). Bindings, e.g.:")
    for eid in ("m-rev", "items", "toggle"):
        print("     ", eid, compact({k: v for k, v in tpl["elements"][eid].items() if k != "children"}, 118))
    for op in ops[1:]:
        print(f"op: {op['op']} {op['path']:<18} {compact(op['value'], 80)}")
    res = jr.official_check(json.dumps(tpl), "base")
    print("@json-render/core validateSpec + catalog Zod props:", "skipped" if res is None else ("valid" if res["ok"] else res["issues"]))
    print("action restock_beans ->", compact(json.loads(post(f"{url}/jr/action", {"action": "restock_beans", "params": {"kg": 10},
                                                                                     "state": {"inventory": {"beans_kg": 3.5}}})), 120))
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=Oat latte")
            page.click("text=Hide top items")           # built-in setState: no server round trip
            page.wait_for_selector("text=Show top items")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=13.5 kg")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
