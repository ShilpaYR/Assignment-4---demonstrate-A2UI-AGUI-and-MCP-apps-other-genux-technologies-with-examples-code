"""The coffee-cart UI as OpenUI Lang programs (used to author the fixtures).

OpenUI Lang is line-oriented: ``name = Component(arg1, arg2, ...)``, one
statement per line, arguments are positional, and a name may be used
*before* the line that defines it (forward references). Strings are
JSON-style literals, so ``json.dumps`` writes them safely.
"""

from __future__ import annotations

import json
import sys
from pathlib import Path

sys.path.insert(0, str(Path(__file__).resolve().parents[2]))

from common import scenario as s  # noqa: E402
from common.specs import break_even_html  # noqa: E402


def lit(value) -> str:
    return json.dumps(value, ensure_ascii=False)


def static_program() -> str:
    k, t = s.kpis(), s.items_table()
    cups = format(k["cups"], ",")
    return "\n".join([
        "root = Stack([dash, stock])",
        f"dash = SalesDashboard({lit(s.CART_NAME + ' - this week')}, {lit(s.money(k['revenue']))}, {lit(k['revenue_delta'])}, "
        f"{lit(cups)}, {lit(s.money(k['avg_ticket']))}, {lit(s.week_labels())}, {lit(s.week_revenue())}, {lit(t['rows'])})",
        f"stock = InventoryCard({s.INVENTORY['beans_kg']}, {s.INVENTORY['reorder_point_kg']})",
    ]) + "\n"


def _dashboard_lines(hybrid: bool) -> list[str]:
    k, t = s.kpis(), s.items_table()
    beans_text = f"Beans on hand: {s.INVENTORY['beans_kg']} kg (reorder at 5 kg)."
    children = "[kpis, whatif, chart, items, stock]" if hybrid else "[kpis, chart, items, stock]"
    lines = [
        "root = Stack([dash])",
        f"dash = Card({lit(s.CART_NAME + ' - this week')}, {children})",
        "kpis = Row([rev, cups, ticket])",
        f"rev = Metric(\"Revenue\", {lit(s.money(k['revenue']))}, {lit(k['revenue_delta'])})",
        f"cups = Metric(\"Cups sold\", {lit(format(k['cups'], ','))}, {lit(k['cups_delta'])})",
        f"ticket = Metric(\"Avg ticket\", {lit(s.money(k['avg_ticket']))})",
    ]
    if hybrid:
        lines.append(f"whatif = HtmlArtifact(\"What-if price calculator\", {lit(break_even_html())})")
    lines += [
        f"chart = BarChart(\"Revenue by day (USD)\", {lit(s.week_labels())}, {lit(s.week_revenue())})",
        f"items = Table({lit(t['columns'])}, {lit(t['rows'])})",
        "stock = Row([beans, restock])",
        f"beans = Text({lit(beans_text)}, \"strong\")",
        "restock = Button(\"Reorder 10 kg of beans\", \"restock_beans\")",
    ]
    return lines


def declarative_program() -> str:
    return "\n".join(_dashboard_lines(False)) + "\n"


def hybrid_program() -> str:
    return "\n".join(_dashboard_lines(True)) + "\n"


def html_program() -> str:
    return "root = Stack([calc])\n" + f"calc = HtmlArtifact(\"Break-even calculator\", {lit(break_even_html())})\n"
