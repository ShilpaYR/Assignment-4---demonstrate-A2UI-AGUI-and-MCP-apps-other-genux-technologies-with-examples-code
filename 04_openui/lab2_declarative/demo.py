"""Recorded demo for OpenUI lab 2 (declarative): forward references while streaming + a format/token comparison."""
import json
import os
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
ROOT = HERE.parents[1]
sys.path[:0] = [str(ROOT), str(HERE), str(ROOT / "03_json_render" / "shared")]

from common import tokens  # noqa: E402
from common.demo import banner, browser_page, post, snap, start  # noqa: E402
from common.web import read_sse  # noqa: E402
import server  # noqa: E402
import oui  # noqa: E402
import specs as jr_specs  # noqa: E402  (json-render spec builders, Part 3)


def nested(spec, eid):
    """The same UI as a classic nested JSON tree (children inline)."""
    el = spec["elements"][eid]
    return {"type": el["type"], "props": el["props"], "children": [nested(spec, c) for c in el["children"]]}


def main():
    banner("Part 4 / Lab 4.2 - OpenUI Lang declarative: primitives, forward references, streaming")
    url = start(server.build_app())
    events = read_sse(post(f"{url}/oui/stream", {}))
    program = "".join(e.get("delta", "") for e in events)
    print("program (the model's whole answer):")
    for line in program.splitlines():
        print("  " + (line if len(line) < 104 else line[:101] + "..."))
    lines = program.splitlines()
    for n in (2, 4, 8):
        partial = oui.official_parse("\n".join(lines[:n]) + "\n", "declarative")
        if partial:
            print(f"after {n:>2} lines: {partial['elements']:>2} elements rendered, unresolved forward refs = {partial['meta']['unresolved']}")
    spec = jr_specs.dashboard_spec()
    spec.pop("state")
    compact = lambda o: json.dumps(o, separators=(",", ":"))  # noqa: E731
    rows = [
        ("OpenUI Lang (this lab)", program),
        ("json-render spec (flat JSON)", compact(spec)),
        ("json-render SpecStream (JSONL)", "\n".join(compact(op) for op in jr_specs.to_patches(spec))),
        ("nested JSON tree", compact(nested(spec, spec["root"]))),
    ]
    print(f"same dashboard, output size ({tokens.method()}):")
    base = tokens.count(program)
    for name, text in rows:
        n = tokens.count(text)
        print(f"  {name:<32} {len(text):>5} chars {n:>5} tokens  {n / base:4.2f}x")
    print("action restock_beans -> edit:", json.loads(post(f"{url}/oui/action", {"action": "restock_beans"}))["patch"].strip())
    os.environ["GENUX_STREAM_DELAY"] = "0.08"     # slow the scripted model down so the partial state is visible
    with browser_page() as page:
        if page:
            page.goto(url)
            page.wait_for_function("document.body.innerText.includes('not defined yet: items, stock')")
            snap(page, HERE, "screenshot_partial.png")
            page.wait_for_selector("text=done:")
            page.click("[data-action=restock_beans]")
            page.wait_for_selector("text=10 kg ordered")
            snap(page, HERE, "screenshot.png")


if __name__ == "__main__":
    main()
