"""Recorded demo for json-render lab 2 (declarative): SpecStream validated line by line."""
import json
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE)]

from common.demo import banner, browser_page, compact, post, snap, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import jr  # noqa: E402


def main():
    banner("Part 3 / Lab 3.2 - json-render declarative: SpecStream patches, validated as they stream")
    print(f"system prompt = catalog.prompt() from @json-render/core: {len(server.SYSTEM):,} chars; components section:")
    for line in [l for l in server.SYSTEM.splitlines() if l.startswith("- ")][:4]:
        print("  | " + line[:100])
    url = start(server.build_app())
    events = read_sse(post(f"{url}/jr/stream", {}))
    for e in events:
        if "op" in e:
            print(f"  accepted {e['op']} {e['path']}")
        elif not e.get("done"):
            print(f"  REJECTED {e['rejected']}: {e['errors'][0]}")
    summary = events[-1]
    print("summary:", compact({k: summary[k] for k in ("elements", "rejected", "issues", "server_first_element_ms", "server_total_ms")}, 160))
    fixture = (HERE / "fixtures" / "dashboard.jsonl").read_text()
    raw = jr.official_check(fixture, "base", stream=True)
    print("official compileSpecStream on the RAW model output :", "skipped" if raw is None else (raw["issues"] or "valid"))
    accepted = "\n".join(json.dumps(e) for e in events if "op" in e)
    ok = jr.official_check(accepted, "base", stream=True)
    if ok is not None:
        print("official compileSpecStream on the ACCEPTED patches:", ok["issues"] or "valid",
              "| same spec as Python:", ok["spec"] == jr.apply_stream(accepted))
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_selector("text=first element painted")
            print("browser:", page.locator("#status").inner_text())
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
