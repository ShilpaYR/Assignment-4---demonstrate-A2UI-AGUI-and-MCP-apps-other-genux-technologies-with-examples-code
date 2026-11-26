"""Recorded demo for AG-UI lab 4 (mixed): hybrid layout + three round trips back to the agent."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))
sys.path.insert(0, str(HERE))

from common.demo import agui_input, banner, browser_page, compact, inner_frame, post_sse, snap, start  # noqa: E402
from common.jsonpatch import apply  # noqa: E402
import server  # noqa: E402

TOOLS = [{"name": "confirm_restock", "description": "approve", "parameters": {"type": "object"}}]


def main():
    banner("Part 1 / Lab 4 - AG-UI, mixed mode: catalog + sandboxed region + human in the loop")
    url = start(server.build_app()) + "/agui"
    prompt = server.scenario.MIXED_PROMPT

    ev = post_sse(url, agui_input(prompt, tools=TOOLS))
    state = next(e for e in ev if e["type"] == "STATE_SNAPSHOT")["snapshot"]
    kinds = [f"{k}:{v['type']}" for k, v in state["ui"]["elements"].items()]
    print("run 1 (request)      ->", [e["type"] for e in ev])
    print("   state.ui elements:", ", ".join(kinds))

    ev = post_sse(url, agui_input(prompt, state=state, tools=TOOLS, forwarded={"action": "restock_beans", "params": {"kg": 10}}))
    call = next(e for e in ev if e["type"] == "TOOL_CALL_START")
    args = json.loads("".join(e["delta"] for e in ev if e["type"] == "TOOL_CALL_ARGS"))
    print("run 2 (Button action)->", [e["type"] for e in ev if not e["type"].startswith("TEXT")])
    print(f"   agent calls the PAGE's tool {call['toolCallName']}({args})")

    msgs = [{"id": "u1", "role": "user", "content": prompt},
            {"id": "a1", "role": "assistant", "toolCalls": [{"id": call["toolCallId"], "type": "function",
             "function": {"name": "confirm_restock", "arguments": json.dumps(args)}}]},
            {"id": "t1", "role": "tool", "toolCallId": call["toolCallId"], "content": json.dumps({"approved": True})}]
    ev = post_sse(url, agui_input(prompt, messages=msgs, state=state, tools=TOOLS))
    delta = next(e for e in ev if e["type"] == "STATE_DELTA")
    state = apply(state, delta["delta"])
    print("run 3 (tool result)  ->", compact(delta, 140))

    ev = post_sse(url, agui_input(prompt, state=state, tools=TOOLS, forwarded={"action": "apply_price", "params": {"price": 3.95}}))
    print("run 4 (sandbox event)->", compact(next(e for e in ev if e["type"] == "STATE_DELTA"), 140))
    ev = post_sse(url, agui_input(prompt, state=state, tools=TOOLS, forwarded={"action": "delete_database"}))
    print("run 5 (unknown action)->", compact(ev[-1], 140))

    with browser_page(height=1000) as page:
        if page:
            page.goto(url.rsplit("/", 1)[0])
            page.wait_for_selector("text=run finished")
            inner_frame(page).wait_for_selector("#apply")
            snap(page, HERE, "screenshot.png")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("#approve")
            snap(page, HERE, "screenshot_confirm.png")
            page.click("#approve")
            page.wait_for_selector("text=Order placed")
            frame = inner_frame(page)
            frame.locator("#price").fill("3.95")
            frame.click("#apply")
            page.wait_for_selector("text=List price set")
            snap(page, HERE, "screenshot_after_actions.png")


if __name__ == "__main__":
    main()
