"""Check that every code snippet in the READMEs exists verbatim in the file it names.

A snippet is a fenced block (```python / ```js / ```html / ```css) whose
preceding non-empty line contains a file path in backticks, e.g.

    `server.py`:
    ```python
    def run(inp): ...
    ```

Each line of the snippet (whitespace-normalised, lines equal to "..." ignored)
must appear in that file. This keeps the walkthroughs honest as code changes.

    python tools/check_snippets.py            # all READMEs
    python tools/check_snippets.py 01_ag_ui   # one part
"""
import re
import sys
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
FENCE = re.compile(r"^```(python|js|javascript|html|css)\s*$")
CHECKED = 0


def norm(s):
    return " ".join(s.split())


def check(readme: Path) -> list[str]:
    global CHECKED
    problems, lines = [], readme.read_text(encoding="utf-8").splitlines()
    i = 0
    while i < len(lines):
        m = FENCE.match(lines[i].strip())
        if not m:
            i += 1
            continue
        j = i - 1
        while j >= 0 and not lines[j].strip():
            j -= 1
        names = re.findall(r"`([^`]+\.(?:py|js|mjs|html|css))`", lines[j]) if j >= 0 else []
        end = i + 1
        while end < len(lines) and lines[end].strip() != "```":
            end += 1
        body = [l for l in lines[i + 1:end] if l.strip() and l.strip() != "..."]
        if names:
            target = (readme.parent / names[0])
            if not target.exists():
                problems.append(f"{readme.relative_to(ROOT)}:{i+1}: file {names[0]} not found")
            else:
                text = {norm(l) for l in target.read_text(encoding="utf-8").splitlines()}
                for l in body:
                    if norm(l) not in text:
                        problems.append(f"{readme.relative_to(ROOT)}:{i+1}: line not in {names[0]}: {l.strip()[:80]}")
                CHECKED += 1
        i = end + 1
    return problems


def main():
    parts = sys.argv[1:] or ["."]
    readmes = sorted({p for part in parts for p in (ROOT / part).rglob("README.md") if "node_modules" not in p.parts})
    problems = [p for r in readmes for p in check(r)]
    for p in problems:
        print(p)
    print(f"{len(readmes)} READMEs, {CHECKED} snippets checked, {len(problems)} problems")
    sys.exit(1 if problems else 0)


if __name__ == "__main__":
    main()
