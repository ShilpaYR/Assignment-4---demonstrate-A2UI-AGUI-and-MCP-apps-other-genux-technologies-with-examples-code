"""Recorded demo for OpenUI lab 4 (mixed): primitives + HtmlArtifact; events answered with edits."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, inner_frame, post, snap, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import oui  # noqa: E402


def main():
    banner("Part 4 / Lab 4.4 - OpenUI Lang mixed: primitives + one HtmlArtifact, edits by statement")
    url = start(server.build_app())
    events = read_sse(post(f"{url}/oui/stream", {}))
    program = "".join(e.get("delta", "") for e in events)
    for name, expr in oui.statements(program):
        print(f"  {name:<8} = {expr[:88]}{'...' if len(expr) > 88 else ''}")
    s = events[-1]
    print(f"official parser + policy: errors={s['errors']} | {s['tokens']} tokens, HtmlArtifact {s['artifact_tokens']} "
          f"= {100 * s['artifact_tokens'] / s['tokens']:.0f}% ({s['token_method']})")
    for body in ({"action": "apply_price", "params": {"price": 4.2}}, {"action": "restock_beans"},
                 {"action": "apply_price", "params": {"price": 0}}):
        print(f"event {body['action']:<13} ->", compact(json.loads(post(f"{url}/oui/action", body)), 110))
    with browser_page(height=1000) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=done:")
            f = inner_frame(page)
            f.wait_for_selector("#price")
            f.locator("#price").fill("4.2")
            f.click("#apply")
            page.wait_for_selector("text=new list price")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=10 kg ordered")
            print("after both edits the artifact still shows price", inner_frame(page).locator("#priceOut").inner_text(),
                  "(it was not re-mounted)")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
