"""Two surfaces for one harness: a terminal (rich) and a web page (AG-UI over SSE).

Both subscribe to the same harness events. The terminal draws UI tool calls
with ``rich``; the web surface translates every event into AG-UI events:

    run_started  -> RUN_STARTED
    text         -> TEXT_MESSAGE_START / CONTENT / END
    tool_call    -> TOOL_CALL_START / ARGS / END
    tool_result  -> TOOL_CALL_RESULT
    ui           -> STATE_SNAPSHOT / STATE_DELTA (catalog specs) or ACTIVITY_SNAPSHOT (HTML)
    run_finished -> RUN_FINISHED
"""

from __future__ import annotations

import io
import json
import queue
import threading

from ag_ui.core import (
    ActivitySnapshotEvent, EventType, RunErrorEvent, RunFinishedEvent, RunStartedEvent, StateDeltaEvent, StateSnapshotEvent,
    TextMessageContentEvent, TextMessageEndEvent, TextMessageStartEvent, ToolCallArgsEvent, ToolCallEndEvent,
    ToolCallResultEvent, ToolCallStartEvent,
)
from ag_ui.encoder import EventEncoder
from rich import box
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text

from harness import new_id


# ------------------------------------------------------------------ terminal
def render_component(kind: str, p: dict, kids=()):
    """Catalog components -> rich renderables (the terminal 'renderer registry')."""
    if kind == "Card":
        return Panel(Group(*kids), title=f"[bold]{p.get('title', '')}[/]", subtitle=p.get("subtitle"), box=box.ROUNDED)
    if kind == "Row":
        return Columns(list(kids), expand=True, equal=True)
    if kind == "Column":
        return Group(*kids)
    if kind == "Text":
        return Text(p.get("text", ""), style={"muted": "dim", "strong": "bold"}.get(p.get("tone") or "", ""))
    if kind == "Metric":
        delta = f"  [green]{p['delta']}[/]" if p.get("delta") else ""
        return Panel(f"[bold]{p.get('value')}[/]{delta}", title=p.get("label"), box=box.SQUARE, width=26)
    if kind == "BarChart":
        top = max(p.get("values") or [1])
        rows = [f"{lab:>4} {'█' * round(26 * v / top):<26} {v:,.0f}" for lab, v in zip(p.get("labels", []), p.get("values", []))]
        return Panel("\n".join(rows), title=p.get("title") or "chart", box=box.SQUARE)
    if kind == "Table":
        t = Table(*p.get("columns", []), box=box.SIMPLE_HEAVY)
        for r in p.get("rows", []):
            t.add_row(*r)
        return t
    if kind == "Button":
        return Text(f"[ {p.get('label')} ]  (action: {p.get('action')})", style="reverse")
    if kind == "GeneratedView":
        return Panel(f"generated HTML ({len(p.get('html', ''))} chars) - interactive in the web surface only",
                     title=p.get("title"), style="magenta", box=box.DOUBLE)
    return Text(f"(unknown component {kind})", style="red")


def render_spec(spec: dict, eid: str | None = None):
    eid = eid or spec["root"]
    el = spec["elements"][eid]
    return render_component(el["type"], el.get("props", {}), [render_spec(spec, c) for c in el.get("children", [])])


class TerminalSurface:
    """Prints the run like a terminal coding agent; UI tool calls become rich widgets."""

    STATIC = {"show_metric": "Metric", "show_chart": "BarChart", "show_table": "Table"}

    def __init__(self, width: int = 100):
        self.buffer = io.StringIO()
        self.console = Console(file=self.buffer, width=width, color_system=None, force_terminal=False)

    def __call__(self, kind: str, d: dict):
        c = self.console
        if kind == "run_started":
            c.print(Text(f"> {d['user']}"))                  # Text(): "[ui action]" is not rich markup
        elif kind == "text":
            c.print(Text(f"assistant: {d['text']}"))
        elif kind == "tool_call":
            args = json.dumps(d["arguments"])
            c.print(Text(f"  tool {d['name']}({args[:70] + '...' if len(args) > 70 else args})"))
        elif kind == "tool_result" and not d["ok"]:
            c.print(Text(f"  ! {d['name']} failed: {json.dumps(d['result'])[:150]}"))
        elif kind == "ui":
            c.print(self.ui(d))

    def ui(self, d: dict):
        a = d["arguments"]
        if d["tool"] in self.STATIC:
            return render_component(self.STATIC[d["tool"]], a)
        if "spec" in d["result"]:
            return render_spec(d["result"]["spec"])
        if "ops" in d["result"]:
            return Text(f"  (UI on screen patched: {', '.join(op['path'] for op in d['result']['ops'])})", style="dim")
        if "html" in d["result"]:
            return Panel(f"{d['result']['title']}: saved to {d['result']['path']} ({d['result']['tokens']} tokens)\n"
                         "open it in a browser, or use the web surface (--web)", title="render_html", box=box.DOUBLE)
        return Text(json.dumps(d["result"])[:200])

    def text(self) -> str:
        return self.buffer.getvalue()


# ------------------------------------------------------------------ web (AG-UI)
class AguiSurface:
    """Translates harness events into AG-UI events on a queue (one per run)."""

    def __init__(self, thread_id: str, run_id: str):
        self.q: queue.Queue = queue.Queue()
        self.thread_id, self.run_id = thread_id, run_id
        self.state: dict = {}

    def put(self, event):
        self.q.put(event)

    def __call__(self, kind: str, d: dict):
        if kind == "run_started":
            self.put(RunStartedEvent(type=EventType.RUN_STARTED, thread_id=self.thread_id, run_id=self.run_id))
        elif kind == "text":
            mid = new_id("msg")
            self.put(TextMessageStartEvent(type=EventType.TEXT_MESSAGE_START, message_id=mid, role="assistant"))
            self.put(TextMessageContentEvent(type=EventType.TEXT_MESSAGE_CONTENT, message_id=mid, delta=d["text"]))
            self.put(TextMessageEndEvent(type=EventType.TEXT_MESSAGE_END, message_id=mid))
        elif kind == "tool_call":
            self.put(ToolCallStartEvent(type=EventType.TOOL_CALL_START, tool_call_id=d["id"], tool_call_name=d["name"]))
            self.put(ToolCallArgsEvent(type=EventType.TOOL_CALL_ARGS, tool_call_id=d["id"], delta=json.dumps(d["arguments"])))
            self.put(ToolCallEndEvent(type=EventType.TOOL_CALL_END, tool_call_id=d["id"]))
        elif kind == "tool_result":
            content = d["result"] if isinstance(d["result"], str) else json.dumps(d["result"])
            self.put(ToolCallResultEvent(type=EventType.TOOL_CALL_RESULT, message_id=new_id("res"), tool_call_id=d["id"],
                                         content=content[:2000], role="tool"))
        elif kind == "ui":
            self.ui(d)
        elif kind == "run_finished":
            self.put(RunFinishedEvent(type=EventType.RUN_FINISHED, thread_id=self.thread_id, run_id=self.run_id))
            self.put(None)

    def ui(self, d: dict):
        r = d["result"]
        if "spec" in r:
            self.state = {"ui": r["spec"]}
            self.put(StateSnapshotEvent(type=EventType.STATE_SNAPSHOT, snapshot=self.state))
        elif "ops" in r:
            self.put(StateDeltaEvent(type=EventType.STATE_DELTA, delta=r["ops"]))
        elif "html" in r:
            self.put(ActivitySnapshotEvent(type=EventType.ACTIVITY_SNAPSHOT, message_id=new_id("act"),
                                           activity_type="genux.sandboxed_html", content={"title": r["title"], "html": r["html"], "tokens": r["tokens"]}))
        # static tool calls need nothing extra: the page renders TOOL_CALL_* for show_* tools itself


def stream_run(harness, user_text: str, thread_id: str, run_id: str):
    """Run the harness in a thread; yield encoded AG-UI events as they happen (SSE)."""
    surface = AguiSurface(thread_id, run_id)
    harness.listeners = [l for l in harness.listeners if not isinstance(l, AguiSurface)] + [surface]

    def run():
        try:
            harness.run(user_text)
        except Exception as exc:  # never leave the page waiting: RUN_ERROR ends the stream
            surface.put(RunErrorEvent(type=EventType.RUN_ERROR, message=f"{type(exc).__name__}: {exc}"))
            surface.put(None)

    threading.Thread(target=run, daemon=True).start()
    encoder = EventEncoder()
    while (event := surface.q.get()) is not None:
        yield encoder.encode(event)
