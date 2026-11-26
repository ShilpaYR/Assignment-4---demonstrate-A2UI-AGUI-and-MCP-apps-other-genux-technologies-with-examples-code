"""Recorded demo for harness lab 4 (mixed): UI clicks become turns of the same agent conversation."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common import scenario  # noqa: E402
from common.demo import agui_input, banner, browser_page, compact, inner_frame, post, post_sse, snap, start  # noqa: E402
from surfaces import TerminalSurface  # noqa: E402
from web import build_web  # noqa: E402
import agent  # noqa: E402


def main():
    banner("Part 6 / Lab 6.4 - harness mixed: the whole loop, with the human in it")
    h = agent.build_harness()
    term = TerminalSurface(width=96)
    url = start(build_web(h.on(term), title="Lab 4 - the whole loop, human in it", mode="mixed",
                          prompt=scenario.MIXED_PROMPT, actions=agent.UI_EVENTS))
    runs = [agui_input(scenario.MIXED_PROMPT),
            agui_input("", messages=[], forwarded={"action": "restock_beans", "params": {"kg": 10}}),
            agui_input("", messages=[], forwarded={"action": "apply_price", "params": {"price": 4.2}})]
    for inp in runs:
        events = post_sse(f"{url}/agui", inp)
        label = inp["forwardedProps"].get("action", "request")
        print(f"run '{label}': tools {[e['toolCallName'] for e in events if e['type'] == 'TOOL_CALL_START']}, "
              f"UI events {[e['type'] for e in events if e['type'].startswith(('STATE', 'ACTIVITY'))]}")
        for e in events:
            if e["type"] == "STATE_DELTA":
                print("    STATE_DELTA", compact(e["delta"][0], 110))
    print("the conversation now has", len(h.messages), "messages; user turns:",
          [m["content"][:45] for m in h.messages if m["role"] == "user"])
    print("inventory.json in the agent's workspace:", json.loads(h.workspace.path("inventory.json").read_text()))
    print("refused action:", post(f"{url}/agui", agui_input("", messages=[], forwarded={"action": "rm_rf"})))
    print("--- the terminal surface saw the same runs (last lines):")
    print("\n".join(term.text().rstrip().splitlines()[-6:]))

    url2 = start(build_web(agent.build_harness(), title="Lab 4 - the whole loop, human in it", mode="mixed",
                           prompt=scenario.MIXED_PROMPT, actions=agent.UI_EVENTS))
    with browser_page(height=1150) as page:
        if page:
            page.goto(url2)
            page.wait_for_selector("text=run finished")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=order #1 placed")
            f = inner_frame(page)
            f.locator("#price").fill("4.2")
            f.click("#apply")
            page.wait_for_selector("text=new list price")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
