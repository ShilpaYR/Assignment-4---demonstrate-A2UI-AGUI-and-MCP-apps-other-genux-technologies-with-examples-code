"""Start all 24 lab servers at once (for recording a video), each on its default port.

    python tools/start_all.py          # Ctrl+C stops them all

Ports: part P, lab L -> 80P L  (AG-UI 8011-8014, A2UI 8021-8024, json-render 8031-8034,
OpenUI 8041-8044, MCP Apps 8051-8054, harness 8061-8064).
"""
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]


def command(lab: Path) -> list[str]:
    if (lab / "run_host.py").exists():
        return [sys.executable, "run_host.py"]                    # MCP Apps: our host + the MCP server
    if (lab / "agent.py").exists():
        return [sys.executable, "agent.py"] + ([] if lab.name == "lab4_mixed" else ["--web"])  # harness
    return [sys.executable, "server.py"]


def main():
    procs = []
    for lab in sorted(ROOT.glob("[0-9][0-9]_*/lab*")):
        if lab.is_dir() and (lab / "demo.py").exists():
            port = f"80{lab.parent.name[1]}{lab.name[3]}"
            procs.append(subprocess.Popen(command(lab), cwd=lab, stdout=subprocess.DEVNULL, stderr=subprocess.STDOUT))
            print(f"http://127.0.0.1:{port}/   {lab.relative_to(ROOT).as_posix()}")
    print(f"\n{len(procs)} servers running. Press Ctrl+C to stop.")
    try:
        while True:
            time.sleep(1)
    except KeyboardInterrupt:
        for p in procs:
            p.terminate()


if __name__ == "__main__":
    main()
