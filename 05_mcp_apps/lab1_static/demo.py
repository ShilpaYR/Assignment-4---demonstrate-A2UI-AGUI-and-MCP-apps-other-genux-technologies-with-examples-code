"""Recorded demo for MCP Apps lab 1 (static): server metadata, the view in a host, the bridge, conformance."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import banner, browser_page, compact, post, snap, start  # noqa: E402
from mcpapps import official_check  # noqa: E402
import run_host  # noqa: E402


def main():
    banner("Part 5 / Lab 5.1 - MCP Apps static: a pre-built view for a tool result")
    url = start(run_host.build_app())                  # starts server.py over stdio behind our host
    for t in json.loads(__import__("urllib.request").request.urlopen(url + "/host/tools").read()):
        print(f"tool {t['name']:<17} _meta.ui = {compact(t['_meta']['ui'])}")
    out = json.loads(post(url + "/host/call", {"name": "coffee_dashboard", "arguments": {"days": 7}, "caller": "model"}))
    res = out["resource"]
    print(f"resources/read {res['uri']}: mimeType={res['mimeType']}, {len(res['text']):,} bytes, _meta={compact(res['_meta'])}")
    print("structuredContent keys (for the view):", sorted(out["result"]["structuredContent"]))
    print("content[0].text (for the model / UI-less hosts):", out["result"]["content"][0]["text"].splitlines()[1][:90])
    print("model calls the app-only tool ->", post(url + "/host/call", {"name": "restock_beans", "arguments": {"kg": 5}, "caller": "model"}))
    with browser_page(height=1100) as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=the bridge is live")
            f = page.frame_locator("iframe.genux-sandbox")
            f.locator("#restock").click()
            f.locator("text=beans: 13.5 kg").wait_for()
            f.locator("#days3").click()
            f.locator("text=last 3 days").wait_for()
            f.locator("#ask").click()
            page.wait_for_selector("text=user message sent by the app")
            snap(page, HERE, "screenshot.png")
            log = page.evaluate("window.__bridgeLog")
            (HERE / "bridge_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
            print("bridge messages:", ", ".join(f"{e['dir'][:4]}:{e['msg'].get('method', 'result')}" for e in log
                                                if e["msg"].get("method") != "ui/notifications/size-changed"))
            check = official_check(log)
            if check:
                print(f"@modelcontextprotocol/ext-apps schemas: {check['checked']} messages checked, errors={check['errors']}")


if __name__ == "__main__":
    main()
