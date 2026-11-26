"""Recorded demo for json-render lab 3 (open-ended): one HtmlBlock, events filtered by its on-map."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, post_sse, snap, start  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def main():
    banner("Part 3 / Lab 3.3 - json-render open-ended: a catalog with only HtmlBlock")
    url = start(server.build_app())
    ops = post_sse(f"{url}/jr/stream", {})
    for op in ops:
        v = op["value"]
        if isinstance(v, dict) and "props" in v:
            v = {**v, "props": {**v["props"], "html": f"<{len(v['props']['html'])} chars>"}}
        print(f"  {op['op']} {op['path']:<18} {compact(v, 120)}")
    report = json.loads(__import__("urllib.request").request.urlopen(f"{url}/jr/tokens").read())
    print(f"the HtmlBlock document is {report['html_tokens']} tokens ({report['method']})")
    res = jr.official_check("\n".join(json.dumps(o) for o in ops), "html", stream=True)
    print("official compileSpecStream + htmlCatalog props:", "skipped" if res is None else (res["issues"] or "valid"))
    print("bad event ->", compact(json.loads(post(f"{url}/jr/action", {"action": "apply_price", "params": {"price": "free"}}))))
    with browser_page() as page:
        if page:
            page.goto(url)
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("3.8")
            f.click("#apply")
            page.wait_for_selector("text=Server stored list price $3.80")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
