"""Recorded demo for AG-UI lab 3 (open-ended): stream HTML, check it, mount it in a sandbox, click inside."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common import tokens  # noqa: E402
from common.demo import agui_input, banner, browser_page, compact, inner_frame, post_sse, snap, start  # noqa: E402
import server  # noqa: E402


def main():
    banner("Part 1 / Lab 3 - AG-UI, open-ended mode: model-written HTML in a sandbox")
    url = start(server.build_app())
    events = post_sse(f"{url}/agui", agui_input(server.scenario.WIDGET_PROMPT))
    chunks = [e for e in events if e["type"] == "TEXT_MESSAGE_CONTENT"]
    print(f"POST /agui -> {len(events)} events ({len(chunks)} TEXT_MESSAGE_CONTENT chunks of raw HTML)")
    print("  " + compact(chunks[0]))
    act = next(e for e in events if e["type"] == "ACTIVITY_SNAPSHOT")
    print("  ACTIVITY_SNAPSHOT:", compact({k: v for k, v in act["content"].items() if k != "html"}, 160))

    root = HERE.parent
    static = json.dumps(json.loads((root / "lab1_static/fixtures/dashboard.json").read_text())[0]["tool_calls"])
    declarative = (root / "lab2_declarative/fixtures/dashboard_spec.json").read_text()
    html = act["content"]["html"]
    print(f"output tokens ({tokens.method()}):")
    print(f"  static      (5 tool calls)        {tokens.count(static):>5}")
    print(f"  declarative (catalog JSON spec)   {tokens.count(declarative):>5}")
    print(f"  open-ended  (HTML document)       {tokens.count(html):>5}   <- one widget, no data table")

    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=run finished")
            frame = inner_frame(page)
            frame.wait_for_selector("#price")
            frame.locator("#price").fill("4.2")      # drag the slider inside the sandbox
            frame.click("#apply")                     # the widget calls genux.emit("apply_price", ...)
            page.wait_for_selector("text=iframe -> page: apply_price")
            print("clicked inside the sandbox -> page received:", page.locator(".wire .entry").last.inner_text()[:120])
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
