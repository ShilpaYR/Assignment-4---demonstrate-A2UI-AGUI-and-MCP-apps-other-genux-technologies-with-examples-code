"""Part 6 / Lab 3 - Harness integration, OPEN-ENDED mode: a render_html tool.

When nothing in a catalog fits, a coding agent can write the interface
itself. ``render_html(title, html)``:

1. checks the document against the HTML policy (no network, no external
   scripts, size limit) - a violation is a tool error the model can fix;
2. saves it as an artifact with the CSP injected first in ``<head>``
   (``artifacts/<name>.html``), so the terminal user can open it;
3. hands it to the surfaces: the web surface mounts it in a sandboxed
   iframe (AG-UI ``ACTIVITY_SNAPSHOT``); the terminal prints where it is.

    python agent.py              # terminal surface (prints the artifact path)
    python agent.py --web        # web surface on http://127.0.0.1:8063
"""

from __future__ import annotations

import argparse
import re
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path[:0] = [str(HERE.parents[1]), str(HERE.parent / "shared")]

from common import scenario, tokens  # noqa: E402
from common.llm import get_llm  # noqa: E402
from common.sandbox import check_html, with_csp  # noqa: E402
from harness import Harness, Tool, Workspace  # noqa: E402

PORT = 8063
ARTIFACTS = HERE / "artifacts"
SYSTEM = ("You are a coding agent. When the user asks for something interactive that no standard component can show, "
          "call render_html with ONE self-contained HTML document (inline CSS/JS, no network). Inside it, "
          "genux.emit('apply_price', {price}) sends a result to the app.")


def render_html(title: str, html: str) -> dict:
    problems = check_html(html)
    if problems:
        return {"error": "render_html rejected the document: " + "; ".join(problems)}
    ARTIFACTS.mkdir(exist_ok=True)
    path = ARTIFACTS / (re.sub(r"[^a-z0-9]+", "-", title.lower()).strip("-") + ".html")
    path.write_text(with_csp(html), encoding="utf-8")      # the saved copy carries its own CSP
    return {"title": title, "html": html, "path": str(path.relative_to(HERE)), "tokens": tokens.count(html)}


RENDER_HTML = Tool("render_html", "Show a self-contained interactive HTML document in a sandbox.",
                   {"type": "object", "properties": {"title": {"type": "string"}, "html": {"type": "string"}},
                    "required": ["title", "html"]}, render_html, ui=True)


def build_harness() -> Harness:
    return Harness(llm=get_llm(HERE / "fixtures"), system=SYSTEM, tools=Workspace().tools() + [RENDER_HTML], fixture="session")


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--web", action="store_true")
    cli.add_argument("--port", type=int, default=PORT)
    args = cli.parse_args()
    harness = build_harness()
    if args.web:
        from web import build_web
        build_web(harness, title="Lab 3 - render_html: the agent writes the UI", mode="open-ended", prompt=scenario.WIDGET_PROMPT).serve(args.port)
    else:
        from surfaces import TerminalSurface
        term = TerminalSurface()
        harness.on(term).run(scenario.WIDGET_PROMPT)
        print(term.text())
