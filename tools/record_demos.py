"""Run every lab's demo.py, save its output and paste it into the lab README.

For each lab folder (``NN_part/labN_mode``):
  * runs ``python demo.py`` (scripted model, real servers, real browser),
  * writes ``demo_output.txt`` next to it,
  * replaces the block between ``<!-- demo-output:start -->`` and
    ``<!-- demo-output:end -->`` in the lab README with that output,
  * appends a line per lab to ``evidence/DEMO_LOG.md``.

    python tools/record_demos.py              # every lab
    python tools/record_demos.py 02_a2ui      # one part
"""
import datetime as dt
import os
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
START, END = "<!-- demo-output:start -->", "<!-- demo-output:end -->"


def labs(filters):
    for demo in sorted(ROOT.glob("[0-9][0-9]_*/lab*/demo.py")):
        rel = str(demo.parent.relative_to(ROOT))
        if not filters or any(rel.startswith(f) for f in filters):
            yield demo.parent


def main():
    filters = sys.argv[1:]
    log = [f"# Demo log\n\nRecorded {dt.datetime.now():%Y-%m-%d %H:%M} on {platform.system()} "
           f"with Python {platform.python_version()}. Each lab ran `python demo.py` (scripted model replies).\n",
           "| Lab | Result | Seconds | Screenshots |", "|---|---|---:|---|"]
    failed = 0
    for lab in labs(filters):
        t0 = time.time()
        env = {**os.environ, "PYTHONIOENCODING": "utf-8"}
        proc = subprocess.run([sys.executable, "demo.py"], cwd=lab, capture_output=True, text=True, env=env, timeout=300)
        secs = time.time() - t0
        out = proc.stdout.rstrip() + ("\n" + proc.stderr.rstrip() if proc.returncode else "")
        (lab / "demo_output.txt").write_text(out + "\n", encoding="utf-8")
        readme = lab / "README.md"
        if readme.exists():
            text = readme.read_text(encoding="utf-8")
            if START in text:
                block = f"{START}\n```text\n$ python demo.py\n{out}\n```\n{END}"
                text = re.sub(re.escape(START) + r".*?" + re.escape(END), lambda _: block, text, flags=re.S)
                readme.write_text(text, encoding="utf-8")
        shots = ", ".join(sorted(p.name for p in lab.glob("screenshot*.png")))
        ok = proc.returncode == 0
        failed += not ok
        rel = lab.relative_to(ROOT).as_posix()
        log.append(f"| [{rel}](../{rel}/) | {'PASS' if ok else 'FAIL'} | {secs:.1f} | {shots} |")
        print(f"{'PASS' if ok else 'FAIL'}  {rel}  ({secs:.1f}s)")
        if not ok:
            print(out[-1500:])
    if not filters:
        (ROOT / "evidence").mkdir(exist_ok=True)
        (ROOT / "evidence" / "DEMO_LOG.md").write_text("\n".join(log) + "\n", encoding="utf-8")
    sys.exit(1 if failed else 0)


if __name__ == "__main__":
    main()
