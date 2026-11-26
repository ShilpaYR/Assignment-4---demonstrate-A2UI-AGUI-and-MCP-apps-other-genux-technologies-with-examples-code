"""Recorded demo for MCP Apps lab 4 (mixed): hybrid view, app-only tools, model context, and a text-only host."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import banner, browser_page, post, snap, start  # noqa: E402
from mcpapps import official_check  # noqa: E402
import run_host  # noqa: E402
import text_host  # noqa: E402


def main():
    banner("Part 5 / Lab 5.4 - MCP Apps mixed: catalog + generated region, two hosts")
    print(text_host.run(HERE / "server.py", "coffee_dashboard_hybrid", {"request": "dashboard"}))
    url = start(run_host.build_app())
    for body in ({"name": "apply_price", "arguments": {"price": 4.0}, "caller": "model"},
                 {"name": "apply_price", "arguments": {"price": 40}, "caller": "app"}):
        r = json.loads(post(url + "/host/call", body))
        print(f"[web host] {body['caller']:>5} -> apply_price({body['arguments']['price']}):", r.get("error") or r["result"]["content"][0]["text"])
    with browser_page(height=1150) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=the bridge is live")
            view = page.frame_locator("iframe.genux-sandbox")
            calc = view.frame_locator("iframe.genux-sandbox")
            calc.locator("#price").fill("4.05")
            calc.locator("#apply").click()
            view.locator("text=new list price").wait_for()
            view.locator("[data-action=restock_beans]").click()
            view.locator("text=order placed").wait_for()
            print("[web host] after both tool calls the nested calculator still shows", calc.locator("#priceOut").inner_text())
            print("[web host]", page.locator("#status").inner_text())
            snap(page, HERE, "screenshot.png")
            log = page.evaluate("window.__bridgeLog")
            (HERE / "bridge_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
            calls = [e["msg"]["params"]["name"] for e in log if e["msg"].get("method") == "tools/call"]
            print("[web host] view -> host tools/call:", calls)
            check = official_check(log)
            if check:
                print(f"@modelcontextprotocol/ext-apps schemas: {check['checked']} bridge messages checked, errors={check['errors']}")


if __name__ == "__main__":
    main()
