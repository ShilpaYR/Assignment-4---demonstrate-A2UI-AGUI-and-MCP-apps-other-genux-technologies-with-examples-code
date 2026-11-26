"""Recorded demo for MCP Apps lab 3 (open-ended): server-side generation, nested sandbox, model context."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared"), str(HERE)]

from common.demo import banner, browser_page, post, snap, start  # noqa: E402
from mcpapps import official_check  # noqa: E402
import run_host  # noqa: E402


def main():
    banner("Part 5 / Lab 5.3 - MCP Apps open-ended: generated HTML, two sandboxes deep")
    url = start(run_host.build_app())
    out = json.loads(post(url + "/host/call", {"name": "generate_widget", "arguments": {"request": "break-even calculator"}, "caller": "model"}))
    sc = out["result"]["structuredContent"]
    print("content[0].text:", out["result"]["content"][0]["text"])
    print(f"structuredContent: title={sc['title']!r}, html={len(sc['html'])} chars, allowedEvents={sc['allowedEvents']}")
    print("view resource _meta.ui.csp:", out["resource"]["_meta"]["ui"]["csp"], "(no network for the view)")
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=the bridge is live")
            inner = page.frame_locator("iframe.genux-sandbox").frame_locator("iframe.genux-sandbox")
            inner.locator("#price").fill("4.4")
            inner.locator("#apply").click()
            page.wait_for_selector("text=model context updated")
            print("nesting: host page > view iframe > widget iframe; frames on the page:", len(page.frames))
            print("host status:", page.locator("#status").inner_text())
            state = json.loads(__import__("urllib.request").request.urlopen(url + "/host/state").read())
            print("what the model will see next turn (host state):", state["context"][0]["text"])
            snap(page, HERE, "screenshot.png")
            log = page.evaluate("window.__bridgeLog")
            (HERE / "bridge_log.json").write_text(json.dumps(log, indent=1), encoding="utf-8")
            check = official_check(log)
            if check:
                print(f"@modelcontextprotocol/ext-apps schemas: {check['checked']} bridge messages checked, errors={check['errors']}")


if __name__ == "__main__":
    main()
