"""The one scenario every lab uses: the Campus Coffee Cart.

Keeping the data identical across all 24 labs makes the comparison fair:
the only thing that changes from lab to lab is *how* the agent describes
the interface (static / declarative / open-ended / mixed) and *which*
technology carries it (AG-UI, A2UI, json-render, OpenUI, MCP Apps, harness).
"""

from __future__ import annotations

import copy

CART_NAME = "Campus Coffee Cart"

# (day, cups sold, revenue in USD)
WEEK = [
    ("Mon", 182, 655.20),
    ("Tue", 205, 738.00),
    ("Wed", 231, 831.60),
    ("Thu", 198, 712.80),
    ("Fri", 264, 950.40),
    ("Sat", 121, 435.60),
    ("Sun", 96, 345.60),
]

# (item, cups, revenue)
TOP_ITEMS = [
    ("Oat latte", 402, 1849.20),
    ("Cold brew", 318, 1240.20),
    ("Espresso", 236, 637.20),
    ("Chai", 141, 542.10),
]

INVENTORY = {"beans_kg": 3.5, "reorder_point_kg": 5.0, "milk_l": 22.0}

# The three requests the labs send to the model.
DASHBOARD_PROMPT = f"Show this week's sales dashboard for the {CART_NAME}."
WIDGET_PROMPT = (
    "Build an interactive break-even calculator for the coffee cart: "
    "sliders for price per cup, cost per cup and fixed weekly costs."
)
MIXED_PROMPT = (
    "Show this week's dashboard, and add an interactive what-if price calculator "
    "that the standard components cannot express."
)


def kpis() -> dict:
    cups = sum(c for _, c, _ in WEEK)
    revenue = sum(r for _, _, r in WEEK)
    best = max(WEEK, key=lambda d: d[2])
    return {
        "revenue": round(revenue, 2),
        "cups": cups,
        "avg_ticket": round(revenue / cups, 2),
        "best_day": best[0],
        "revenue_delta": "+8.4%",
        "cups_delta": "+5.1%",
    }


def money(x: float) -> str:
    return f"${x:,.2f}"


def week_labels() -> list[str]:
    return [d for d, _, _ in WEEK]


def week_revenue() -> list[float]:
    return [r for _, _, r in WEEK]


def items_table() -> dict:
    return {
        "columns": ["Item", "Cups", "Revenue"],
        "rows": [[n, str(c), money(r)] for n, c, r in TOP_ITEMS],
    }


def inventory() -> dict:
    return copy.deepcopy(INVENTORY)


def as_text() -> str:
    """Plain-text fallback, used by hosts that cannot render UI."""
    k = kpis()
    lines = [
        f"{CART_NAME} - this week",
        f"Revenue {money(k['revenue'])} ({k['revenue_delta']}), cups {k['cups']} ({k['cups_delta']}), "
        f"avg ticket {money(k['avg_ticket'])}, best day {k['best_day']}.",
        "Top items: " + ", ".join(f"{n} {c}" for n, c, _ in TOP_ITEMS) + ".",
        f"Beans on hand {INVENTORY['beans_kg']} kg (reorder point {INVENTORY['reorder_point_kg']} kg).",
    ]
    return "\n".join(lines)
