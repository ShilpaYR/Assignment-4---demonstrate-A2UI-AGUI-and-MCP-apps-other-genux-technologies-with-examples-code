"""Run this lab inside our browser host:  python run_host.py   ->  http://127.0.0.1:8052"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from host import build_host  # noqa: E402  (shared/host.py)

PORT = 8052


def build_app():
    return build_host(HERE, title="Lab 2 - the view is a catalog renderer", mode="declarative",
                      prompt="Show this week's sales dashboard for the Campus Coffee Cart.",
                      tool="render_dashboard", arguments={"request": "Show this week's sales dashboard for the Campus Coffee Cart."})


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
