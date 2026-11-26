"""json-render helpers shared by the four Part-3 labs.

json-render (Vercel Labs) describes a UI as a flat **spec**:

    {"root": "dash", "elements": {"dash": {"type": "Card", "props": {...}, "children": [...]}}, "state": {...}}

Elements can read state with ``{"$state": "/path"}``, bind inputs with
``{"$bindState": "/path"}``, show/hide with ``"visible"`` and react to events
with ``"on": {"press": {"action": "...", "params": {...}}}``. Models stream a
spec as **SpecStream**: JSONL lines, each an RFC 6902 JSON Patch operation.

The catalogs are defined once with the official library in ``catalog.mjs``.
``node build.mjs`` exports from them the prompts and, per component, a JSON
Schema of its Zod props (``generated/``). This module validates with those
exported schemas in Python, and can also ask the official library itself
(``official_check``, needs Node + ``npm install``).
"""

from __future__ import annotations

import json
import shutil
import subprocess
import sys
from functools import lru_cache
from pathlib import Path

HERE = Path(__file__).resolve().parent
sys.path.insert(0, str(HERE.parents[1]))

from common import jsonpatch  # noqa: E402

GENERATED = HERE / "generated"


@lru_cache(maxsize=None)
def catalog(name: str = "base") -> dict:
    return json.loads((GENERATED / f"schema_{name}.json").read_text(encoding="utf-8"))


def prompt(name: str = "base") -> str:
    return (GENERATED / f"prompt_{name}.txt").read_text(encoding="utf-8")


def _is_expression(value) -> bool:
    return isinstance(value, dict) and any(k.startswith("$") for k in value)


def _props_for_validation(props: dict, schema: dict) -> dict:
    """Expressions ($state, $bindState, $cond ...) resolve at render time: skip them. Nullable props may be omitted."""
    out = {k: v for k, v in props.items() if not _is_expression(v)}
    for name, sub in schema.get("properties", {}).items():
        types = sub.get("type")
        nullable = isinstance(types, list) and "null" in types
        if name not in out and (nullable or _is_expression(props.get(name))):
            out[name] = None if nullable else _placeholder(sub)
    return out


def _placeholder(sub):
    return {"string": "", "number": 0, "array": [], "object": {}, "boolean": False}.get(sub.get("type") if isinstance(sub.get("type"), str) else "string", "")


def validate_element(eid: str, el: dict, cat: dict) -> list[str]:
    from jsonschema import Draft202012Validator

    if not isinstance(el, dict) or el.get("type") not in cat["props"]:
        return [f"{eid}: unknown component {el.get('type') if isinstance(el, dict) else el!r}; allowed: {', '.join(cat['props'])}"]
    errors = []
    schema = cat["props"][el["type"]]
    for e in Draft202012Validator(schema).iter_errors(_props_for_validation(el.get("props") or {}, schema)):
        where = "/".join(str(p) for p in e.path) or "props"
        errors.append(f"{eid} ({el['type']}) {where}: {e.message[:140]}")
    allowed = set(cat["actions"]) | set(cat["builtinActions"])
    for event, binding in (el.get("on") or {}).items():
        for b in binding if isinstance(binding, list) else [binding]:
            if b.get("action") not in allowed:
                errors.append(f"{eid}: on.{event} uses action {b.get('action')!r}; allowed: {', '.join(sorted(allowed))}")
    if not isinstance(el.get("children", []), list):
        errors.append(f"{eid}: children must be a list of element keys")
    return errors


def validate(spec: dict, name: str = "base", partial: bool = False) -> list[str]:
    cat = catalog(name)
    if not isinstance(spec, dict) or not isinstance(spec.get("elements"), dict):
        return ["spec needs 'root' and 'elements'"]
    errors = []
    if not partial and spec.get("root") not in spec["elements"]:
        errors.append(f"root {spec.get('root')!r} is not an element")
    for eid, el in spec["elements"].items():
        errors += validate_element(eid, el, cat)
        if not partial:
            errors += [f"{eid}: child {c!r} does not exist" for c in el.get("children", []) if c not in spec["elements"]]
    return errors


def parse_patch_line(line: str) -> dict | None:
    line = line.strip()
    if not line or line.startswith("```"):
        return None
    op = json.loads(line)
    if op.get("op") not in ("add", "replace", "remove") or not str(op.get("path", "")).startswith("/"):
        raise ValueError(f"not a SpecStream patch: {line[:80]}")
    return op


def apply_stream(text: str) -> dict:
    spec: dict = {}  # same starting point as the library's compileSpecStream
    for line in text.splitlines():
        op = parse_patch_line(line)
        if op:
            spec = jsonpatch.apply(spec, [op])
    return spec


def official_check(payload: str, name: str = "base", stream: bool = False):
    """Validate with @json-render/core itself. Returns None if Node or node_modules are missing."""
    root = HERE.parents[1]
    if not shutil.which("node") or not (root / "node_modules" / "@json-render" / "core").exists():
        return None
    args = ["node", str(HERE / "official.mjs"), name] + (["--stream"] if stream else [])
    proc = subprocess.run(args, input=payload, capture_output=True, text=True, timeout=60)
    return json.loads(proc.stdout) if proc.stdout.strip() else {"ok": False, "issues": [proc.stderr[-400:]]}
