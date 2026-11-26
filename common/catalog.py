"""The shared component catalog and a validator for flat element specs.

Several labs (AG-UI declarative/mixed, MCP Apps declarative/mixed, the
harness labs) use the same *flat element map* shape that json-render and
A2UI use, because it streams well: every element has an id, children are
listed by id, and a child may arrive after its parent.

    {"root": "card-1",
     "elements": {"card-1": {"type": "Card", "props": {"title": "..."}, "children": ["m-1"]},
                  "m-1":    {"type": "Metric", "props": {...}, "children": []}}}

The catalog is the contract. It is used three ways:
  * as the system prompt (``catalog_prompt()``),
  * as the validator (``validate_spec()``),
  * as the renderer registry (the same names in ``common/web/ui.js``).
"""

from __future__ import annotations

import json

# name -> (description, {prop: (type, required)})
CATALOG: dict[str, tuple[str, dict[str, tuple[str, bool]]]] = {
    "Card": ("A titled container. Children go inside.", {"title": ("string", True), "subtitle": ("string", False)}),
    "Row": ("Lays children out side by side.", {}),
    "Column": ("Stacks children vertically.", {}),
    "Text": ("A paragraph. tone is normal, muted or strong.", {"text": ("string", True), "tone": ("string", False)}),
    "Metric": ("One key number with a label and optional delta like '+8%'.",
               {"label": ("string", True), "value": ("string", True), "delta": ("string", False)}),
    "BarChart": ("A bar chart. labels and values have the same length.",
                 {"title": ("string", False), "labels": ("string[]", True), "values": ("number[]", True)}),
    "Table": ("A table; every row has one cell per column.", {"columns": ("string[]", True), "rows": ("string[][]", True)}),
    "Button": ("A button that sends a named action to the server.",
               {"label": ("string", True), "action": ("string", True), "params": ("object", False)}),
}

# The hybrid ("mixed") catalog adds exactly one escape hatch.
GENERATED_VIEW = (
    "A sandboxed region of model-written HTML/CSS/JS. Use ONLY for something the other "
    "components cannot express (an interactive calculator, a custom visual). The document "
    "may call genux.emit(name, payload) to send an event to the app.",
    {"title": ("string", True), "html": ("string", True)},
)


def catalog(hybrid: bool = False) -> dict:
    cat = dict(CATALOG)
    if hybrid:
        cat["GeneratedView"] = GENERATED_VIEW
    return cat


def _type_ok(value, kind: str) -> bool:
    if kind == "string":
        return isinstance(value, str)
    if kind == "number[]":
        return isinstance(value, list) and all(isinstance(v, (int, float)) and not isinstance(v, bool) for v in value)
    if kind == "string[]":
        return isinstance(value, list) and all(isinstance(v, str) for v in value)
    if kind == "string[][]":
        return isinstance(value, list) and all(isinstance(r, list) and all(isinstance(c, str) for c in r) for r in value)
    if kind == "object":
        return isinstance(value, dict)
    return True


def validate_element(eid: str, el: dict, cat: dict, actions: set[str] | None = None) -> list[str]:
    errors = []
    if not isinstance(el, dict):
        return [f"{eid}: element must be an object"]
    kind = el.get("type")
    if kind not in cat:
        return [f"{eid}: unknown component {kind!r}; allowed: {', '.join(cat)}"]
    props = el.get("props") or {}
    if not isinstance(props, dict):
        return [f"{eid}: props must be an object"]
    schema = cat[kind][1]
    for name, (ptype, required) in schema.items():
        if name not in props or props[name] is None:
            if required:
                errors.append(f"{eid}: {kind} needs prop {name!r}")
            continue
        if not _type_ok(props[name], ptype):
            errors.append(f"{eid}: {kind}.{name} must be {ptype}")
    for name in props:
        if name not in schema:
            errors.append(f"{eid}: {kind} has no prop {name!r}")
    if kind == "BarChart" and not errors and len(props["labels"]) != len(props["values"]):
        errors.append(f"{eid}: BarChart labels and values differ in length")
    if kind == "Button" and actions is not None and props.get("action") not in actions:
        errors.append(f"{eid}: action {props.get('action')!r} is not allowed; allowed: {', '.join(sorted(actions))}")
    children = el.get("children", [])
    if not isinstance(children, list) or not all(isinstance(c, str) for c in children):
        errors.append(f"{eid}: children must be a list of element ids")
    return errors


def validate_spec(spec: dict, hybrid: bool = False, actions: set[str] | None = None, partial: bool = False) -> list[str]:
    """Return a list of human-readable errors. ``partial=True`` allows children not yet sent."""
    cat = catalog(hybrid)
    if not isinstance(spec, dict) or not isinstance(spec.get("elements"), dict):
        return ["spec must be an object with 'root' and 'elements'"]
    errors = []
    elements = spec["elements"]
    root = spec.get("root")
    if not partial and root not in elements:
        errors.append(f"root {root!r} is not in elements")
    for eid, el in elements.items():
        errors += validate_element(eid, el, cat, actions)
        if not partial and isinstance(el, dict):
            for child in el.get("children", []) or []:
                if child not in elements:
                    errors.append(f"{eid}: child {child!r} does not exist")
    return errors


def catalog_prompt(hybrid: bool = False, actions: dict[str, str] | None = None) -> str:
    """The system prompt is generated from the catalog, so prompt and validator never drift."""
    lines = [
        "You build user interfaces from a fixed component catalog.",
        'Reply with ONE JSON object: {"root": "<id>", "elements": {"<id>": {"type", "props", "children"}}}.',
        "children is a list of element ids (an empty list when none). Use only these components:",
    ]
    for name, (desc, props) in catalog(hybrid).items():
        sig = ", ".join(f"{p}{'' if req else '?'}: {t}" for p, (t, req) in props.items())
        lines.append(f"- {name}({sig}) - {desc}")
    if actions:
        lines.append("Allowed Button actions: " + "; ".join(f"{k} ({v})" for k, v in actions.items()))
    lines.append("Output JSON only. No markdown fences, no prose.")
    return "\n".join(lines)


def spec_to_patches(spec: dict) -> list[dict]:
    """Turn a complete spec into RFC 6902 'add' operations, parent first (streams top-down)."""
    ops = [{"op": "add", "path": "/root", "value": spec["root"]}]
    seen, order = set(), []

    def walk(eid):
        if eid in seen or eid not in spec["elements"]:
            return
        seen.add(eid)
        order.append(eid)
        for child in spec["elements"][eid].get("children", []):
            walk(child)

    walk(spec["root"])
    order += [e for e in spec["elements"] if e not in seen]
    for eid in order:
        ops.append({"op": "add", "path": f"/elements/{eid}", "value": spec["elements"][eid]})
    return ops


def parse_json_reply(text: str) -> dict:
    from .llm import strip_fences

    return json.loads(strip_fences(text))
