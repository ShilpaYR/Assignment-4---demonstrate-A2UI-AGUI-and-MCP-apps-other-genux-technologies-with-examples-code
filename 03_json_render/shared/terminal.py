"""A second json-render target: the same spec drawn in a terminal with ``rich``.

json-render's selling point is "one catalog, many renderers" (the project
ships React, React Native, terminal/ink and other targets). This file is a
small terminal renderer for the Part-3 catalog: Card -> Panel, Row ->
Columns, Table -> Table, BarChart -> text bars. An HtmlBlock cannot run in a
terminal, so it degrades to a labelled placeholder - which is exactly why
open-ended regions should be optional in a hybrid spec.

    python terminal.py spec.json
"""

from __future__ import annotations

import json
import sys

from rich import box
from rich.columns import Columns
from rich.console import Console, Group
from rich.panel import Panel
from rich.table import Table
from rich.text import Text


def _value(v, state):
    if isinstance(v, dict) and "$cond" in v:
        return _value(v.get("$then") if _visible({"visible": v["$cond"]}, state) else v.get("$else"), state)
    if isinstance(v, dict) and ("$state" in v or "$bindState" in v):
        from common.jsonpatch import get

        try:
            return get(state, v.get("$state") or v.get("$bindState"))
        except (KeyError, IndexError, TypeError):
            return None
    return v


def _visible(el, state) -> bool:
    cond = el.get("visible")
    if cond is None or cond is True:
        return True
    if cond is False:
        return False
    val = _value({"$state": cond["$state"]}, state) if isinstance(cond, dict) and "$state" in cond else True
    if isinstance(cond, dict) and "eq" in cond:
        return val == cond["eq"]
    return bool(val) != bool(isinstance(cond, dict) and cond.get("not"))


def render(spec: dict, eid: str | None = None):
    state = spec.get("state") or {}
    eid = eid or spec["root"]
    el = spec["elements"].get(eid)
    if el is None:
        return Text(f"(waiting for {eid})", style="dim")
    if not _visible(el, state):
        return Text("")
    p = {k: _value(v, state) for k, v in (el.get("props") or {}).items()}
    kids = [render(spec, c) for c in el.get("children", [])]
    kind = el["type"]
    if kind == "Card":
        return Panel(Group(*kids), title=f"[bold]{p.get('title')}[/]", subtitle=p.get("subtitle"), box=box.ROUNDED)
    if kind == "Row":
        return Columns(kids, expand=True, equal=True)
    if kind == "Column":
        return Group(*kids)
    if kind == "Text":
        return Text(str(p.get("text") or ""), style={"muted": "dim", "strong": "bold"}.get(p.get("tone") or "", ""))
    if kind == "Metric":
        delta = f"  [green]{p['delta']}[/]" if p.get("delta") else ""
        return Panel(f"[bold]{p.get('value')}[/]{delta}", title=p.get("label"), box=box.SQUARE, width=26)
    if kind == "BarChart":
        values, top = p.get("values") or [], max(p.get("values") or [1])
        lines = [f"{lab:>4} {'█' * round(28 * v / top):<28} {v:,.0f}" for lab, v in zip(p.get("labels") or [], values)]
        return Panel("\n".join(lines), title=p.get("title") or "chart", box=box.SQUARE)
    if kind == "Table":
        t = Table(*p.get("columns", []), box=box.SIMPLE_HEAVY)
        for row in p.get("rows", []):
            t.add_row(*row)
        return t
    if kind == "Button":
        return Text(f"[ {p.get('label')} ]", style="reverse")
    if kind == "HtmlBlock":
        return Panel(f"interactive HTML ({len(p.get('html') or '')} chars) - open the web view to use it\n{p.get('caption') or ''}",
                     title=f"{p.get('title')} (HtmlBlock)", style="magenta", box=box.DOUBLE)
    return Text(f"(unknown component {kind})", style="red")


def to_text(spec: dict, width: int = 100) -> str:
    import io

    console = Console(file=io.StringIO(), width=width, record=True, color_system=None, force_terminal=False)
    console.print(render(spec))
    return console.export_text()


if __name__ == "__main__":
    sys.path.insert(0, str(__import__("pathlib").Path(__file__).resolve().parents[2]))
    print(to_text(json.loads(open(sys.argv[1], encoding="utf-8").read())))
