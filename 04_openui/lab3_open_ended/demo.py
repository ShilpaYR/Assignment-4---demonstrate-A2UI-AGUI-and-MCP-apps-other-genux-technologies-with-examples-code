"""Recorded demo for OpenUI lab 3 (open-ended): one HtmlArtifact, mounted only once complete."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, snap, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import oui  # noqa: E402


def main():
    banner("Part 4 / Lab 4.3 - OpenUI Lang open-ended: HtmlArtifact only")
    print("library components:", sorted(oui.components("html")))
    url = start(server.build_app())
    events = read_sse(post(f"{url}/oui/stream", {}))
    program = "".join(e.get("delta", "") for e in events)
    for line in program.splitlines():
        print("  " + (line if len(line) < 100 else line[:97] + "..."))
    half = oui.official_parse(program[: len(program) // 2], "html")
    if half:
        calc = half["root"]["props"]["children"][0]
        print(f"official parser on the first half: HtmlArtifact partial={calc['partial']}, document so far {len(calc['props'].get('document', ''))} chars")
    print("server summary:", compact(events[-1], 150))
    for params in ({"price": 4.6}, {"price": "<script>"}):
        print(f"event apply_price {params} ->", json.loads(post(f"{url}/oui/action", {"action": "apply_price", "params": params})))
    os.environ["GENUX_STREAM_DELAY"] = "0.03"
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=the model is still writing this document")
            snap(page, HERE, "screenshot_partial.png")
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("4.6")
            f.click("#apply")
            page.wait_for_selector("text=Server stored list price $4.60")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
