"""Run this lab inside our browser host:  python run_host.py   ->  http://127.0.0.1:8053"""
import argparse
import sys
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parent / "shared"))

from host import build_host  # noqa: E402  (shared/host.py)

PORT = 8053


def build_app():
    return build_host(HERE, title="Lab 3 - model-written HTML, two sandboxes deep", mode="open-ended",
                      prompt="Build an interactive break-even calculator for the coffee cart.",
                      tool="generate_widget", arguments={"request": "Build an interactive break-even calculator for the coffee cart."})


if __name__ == "__main__":
    cli = argparse.ArgumentParser()
    cli.add_argument("--port", type=int, default=PORT)
    build_app().serve(cli.parse_args().port)
