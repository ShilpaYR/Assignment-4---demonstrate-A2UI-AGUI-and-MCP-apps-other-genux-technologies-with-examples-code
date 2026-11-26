"""Recorded demo for harness lab 3 (open-ended): render_html -> artifact file + sandboxed web surface."""
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common import scenario  # noqa: E402
from common.demo import agui_input, banner, browser_page, compact, inner_frame, post_sse, snap, start  # noqa: E402
from surfaces import TerminalSurface  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def main():
    banner("Part 6 / Lab 6.3 - harness open-ended: the agent writes the UI with render_html")
    term = TerminalSurface(width=96)
    agent.build_harness().on(term).run(scenario.WIDGET_PROMPT)
    print("--- surface 1: terminal")
    print(term.text().rstrip())
    saved = (HERE / "artifacts" / "break-even-calculator.html").read_text()
    print("artifact starts with:", saved[saved.index("<head>"):saved.index("<head>") + 95], "...")
    print("policy check of a bad document:", agent.render_html("x", "<script src='https://cdn.example/x.js'></script>")["error"])
    url = start(build_web(agent.build_harness(), title="Lab 3 - render_html: the agent writes the UI", mode="open-ended", prompt=scenario.WIDGET_PROMPT))
    events = post_sse(f"{url}/agui", agui_input(scenario.WIDGET_PROMPT))
    act = next(e for e in events if e["type"] == "ACTIVITY_SNAPSHOT")
    print("--- surface 2: AG-UI ACTIVITY_SNAPSHOT:", compact({k: v for k, v in act["content"].items() if k != "html"}))
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=run finished")
            f = inner_frame(page)
            f.locator("#price").fill("4")
            f.click("#apply")
            page.wait_for_selector("text=iframe -> page: apply_price")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
