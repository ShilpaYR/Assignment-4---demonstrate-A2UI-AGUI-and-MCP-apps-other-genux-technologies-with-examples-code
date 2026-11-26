"""Run this lab inside our browser host:  python run_host.py   ->  http://127.0.0.1:8051"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from host import build_host  # noqa: E402  (shared/host.py)

PORT = 8051


def build_app():
    return build_host(HERE, title="Lab 1 - a pre-built view for a tool result", mode="static",
                      prompt="Show this week's sales dashboard for the Campus Coffee Cart.",
                      tool="coffee_dashboard", arguments={"days": 7})


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
