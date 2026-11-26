"""Run this lab inside our browser host:  python run_host.py   ->  http://127.0.0.1:8054"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from host import build_host  # noqa: E402  (shared/host.py)

PORT = 8054


def build_app():
    return build_host(HERE, title="Lab 4 - catalog + generated region, key on the server", mode="mixed",
                      prompt="Show this week's dashboard, and add an interactive what-if price calculator.",
                      tool="coffee_dashboard_hybrid", arguments={"request": "dashboard with a what-if price calculator"})


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
