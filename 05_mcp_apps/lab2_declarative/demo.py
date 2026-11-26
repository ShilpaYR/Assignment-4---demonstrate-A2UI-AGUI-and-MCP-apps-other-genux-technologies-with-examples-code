"""Recorded demo for MCP Apps lab 2 (declarative): a catalog spec as structuredContent, rendered by a generic view."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import banner, browser_page, compact, post, snap, start  # noqa: E402
from mcpapps import official_check  # noqa: E402
import run_host  # noqa: E402


def main():
    banner("Part 5 / Lab 5.2 - MCP Apps declarative: the view renders a catalog spec")
    url = start(run_host.build_app())
    out = json.loads(post(url + "/host/call", {"name": "render_dashboard", "arguments": {"request": "dashboard"}, "caller": "model"}))
    spec = out["result"]["structuredContent"]["spec"]
    print("content[0].text:", out["result"]["content"][0]["text"])
    print("structuredContent.spec:", ", ".join(f"{k}:{v['type']}" for k, v in spec["elements"].items()))
    print("app-only ui_action from the model ->", post(url + "/host/call", {"name": "ui_action", "arguments": {"action": "restock_beans"}, "caller": "model"}))
    print("app-only ui_action from the app   ->", compact(json.loads(post(url + "/host/call", {"name": "ui_action", "arguments": {"action": "restock_beans", "params": {"kg": 10}}, "caller": "app"}))["result"]["structuredContent"], 120))
    with browser_page(height=1100) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=the bridge is live")
            f = page.frame_locator("iframe.genux-sandbox")
            f.locator("[data-action=restock_beans]").click()
            f.locator("text=10 kg ordered").wait_for()
            snap(page, HERE, "screenshot.png")
            log = page.evaluate("window.__bridgeLog")
            (HERE / "bridge_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
            check = official_check(log)
            if check:
                print(f"@modelcontextprotocol/ext-apps schemas: {check['checked']} bridge messages checked, errors={check['errors']}")


if __name__ == "__main__":
    main()
