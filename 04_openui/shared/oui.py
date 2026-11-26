"""OpenUI Lang helpers shared by the Part-4 labs.

The libraries are defined with the official ``@openuidev/lang-core`` in
``library.mjs``; ``node build.mjs`` generates the prompts and the parser
schemas into ``generated/`` and bundles the official parser for the browser.
Python never re-implements the language: ``official_parse`` runs the real
parser (``parse.mjs``) in Node. ``quick_check`` is a small fallback used
when Node is not installed.
"""

from __future__ import annotations

import json
import re
import shutil
import subprocess
from pathlib import Path

HERE = Path(__file__).resolve().parent
GENERATED = HERE / "generated"
STATEMENT = re.compile(r"^([A-Za-z_]\w*)\s*=\s*(.+)$")
CALL = re.compile(r"\b([A-Z]\w*)\s*\(")


def prompt(name: str) -> str:
    return (GENERATED / f"prompt_{name}.txt").read_text(encoding="utf-8")


def components(name: str) -> set[str]:
    return set(json.loads((GENERATED / f"schema_{name}.json").read_text(encoding="utf-8"))["properties"])


def statements(text: str) -> list[tuple[str, str]]:
    return [(m.group(1), m.group(2)) for line in text.splitlines() if (m := STATEMENT.match(line.strip()))]


def quick_check(text: str, name: str) -> list[str]:
    """Fallback without Node: statement syntax, a root, and only known component names (outside strings)."""
    allowed, errors, names = components(name), [], set()
    for i, line in enumerate(l for l in text.splitlines() if l.strip()):
        m = STATEMENT.match(line.strip())
        if not m:
            errors.append(f"line {i + 1} is not 'name = Expression'")
            continue
        names.add(m.group(1))
        code = re.sub(r'"(?:\\.|[^"\\])*"', '""', m.group(2))   # ignore text inside string literals
        errors += [f"{m.group(1)}: unknown component {c}" for c in CALL.findall(code) if c not in allowed]
    if "root" not in names:
        errors.append("no root statement")
    return errors


def official_parse(text: str, name: str):
    """Parse with @openuidev/lang-core in Node. None if Node / node_modules are missing."""
    root = HERE.parents[1]
    if not shutil.which("node") or not (root / "node_modules" / "@openuidev" / "lang-core").exists():
        return None
    proc = subprocess.run(["node", str(HERE / "parse.mjs"), name], input=text, capture_output=True, text=True, timeout=60)
    return json.loads(proc.stdout) if proc.stdout.strip() else {"ok": False, "meta": {"errors": [proc.stderr[-400:]]}}


def check(text: str, name: str) -> list[str]:
    """Official parser when available, else the quick check."""
    res = official_parse(text, name)
    if res is None:
        return quick_check(text, name)
    meta = res["meta"]
    return [e["message"] for e in meta["errors"]] + [f"unresolved reference {r}" for r in meta["unresolved"]]


def artifact_documents(text: str, name: str) -> list[str]:
    """The HtmlArtifact documents in a program (via the official parser; [] without Node)."""
    res = official_parse(text, name)
    found = []

    def walk(n):
        if isinstance(n, dict) and n.get("type") == "element":
            if n["typeName"] == "HtmlArtifact":
                found.append(n["props"].get("document", ""))
            for v in n["props"].values():
                for item in v if isinstance(v, list) else [v]:
                    walk(item)

    walk((res or {}).get("root"))
    return found
