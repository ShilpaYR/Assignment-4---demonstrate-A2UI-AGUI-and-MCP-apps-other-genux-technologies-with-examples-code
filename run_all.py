"""Run everything and write the evidence report.

    python run_all.py              # tests for all 24 labs + snippet check
    python run_all.py --demos      # also re-record every demo (servers, browser, screenshots)
    python run_all.py 03_json_render   # one part

Each lab is tested in its own pytest process (every lab has its own server.py),
and the results are written to evidence/TEST_REPORT.md.
"""
import argparse
import datetime as dt
import platform
import re
import subprocess
import sys
import time
from pathlib import Path

ROOT = Path(__file__).resolve().parent


def main():
    cli = argparse.ArgumentParser()
    cli.add_argument("parts", nargs="*", help="limit to these part folders, e.g. 01_ag_ui")
    cli.add_argument("--demos", action="store_true", help="re-record demos (needs Playwright + Chromium)")
    args = cli.parse_args()

    if args.demos:
        subprocess.run([sys.executable, "tools/record_demos.py", *args.parts], cwd=ROOT, check=False)

    rows, total_passed, failed_labs = [], 0, []
    for test in sorted(ROOT.glob("[0-9][0-9]_*/lab*/test_lab.py")):
        lab = test.parent
        rel = lab.relative_to(ROOT).as_posix()
        if args.parts and not any(rel.startswith(p) for p in args.parts):
            continue
        t0 = time.time()
        proc = subprocess.run([sys.executable, "-m", "pytest", "test_lab.py", "-rs"], cwd=lab, capture_output=True, text=True)
        tail = (proc.stdout.strip().splitlines() or ["(no output)"])[-1]
        passed = int(m.group(1)) if (m := re.search(r"(\d+) passed", tail)) else 0
        skipped = int(m.group(1)) if (m := re.search(r"(\d+) skipped", tail)) else 0
        total_passed += passed
        ok = proc.returncode == 0
        if not ok:
            failed_labs.append(rel)
            print(proc.stdout[-2000:])
        rows.append(f"| [{rel}]({'../' + rel}/) | {'PASS' if ok else 'FAIL'} | {passed} | {skipped} | {time.time() - t0:.1f}s |")
        print(f"{'PASS' if ok else 'FAIL'}  {rel:<34} {tail}")

    snip = subprocess.run([sys.executable, "tools/check_snippets.py", *args.parts], cwd=ROOT, capture_output=True, text=True)
    print(snip.stdout.strip().splitlines()[-1])

    if not args.parts:
        report = [
            "# Test report", "",
            f"Generated {dt.datetime.now():%Y-%m-%d %H:%M} by `python run_all.py` on {platform.system()}, Python {platform.python_version()}.",
            "Every lab runs offline with scripted model replies; Node-based checks use the official libraries from `npm install`.", "",
            "| Lab | Result | Passed | Skipped | Time |", "|---|---|---:|---:|---:|", *rows, "",
            f"**Total: {total_passed} tests passed in {len(rows)} labs; failures: {len(failed_labs)}.**", "",
            f"Snippet check (every code snippet in every README exists verbatim in the named file): `{snip.stdout.strip().splitlines()[-1]}`",
        ]
        (ROOT / "evidence").mkdir(exist_ok=True)
        (ROOT / "evidence" / "TEST_REPORT.md").write_text("\n".join(report) + "\n", encoding="utf-8")
        print("wrote evidence/TEST_REPORT.md")
    sys.exit(1 if failed_labs or snip.returncode else 0)


if __name__ == "__main__":
    main()
