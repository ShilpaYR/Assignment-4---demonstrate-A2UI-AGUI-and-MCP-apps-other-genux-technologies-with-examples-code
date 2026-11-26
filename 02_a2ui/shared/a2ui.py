"""A2UI v1.0 helpers shared by the four A2UI labs.

A2UI (Agent-to-User Interface, Google) is a *declarative format*: the agent
sends JSON messages that describe a surface; the renderer draws them with
its own native components. Four agent-to-renderer messages matter here:

    createSurface     open a surface, choose its default catalog (may carry components + dataModel inline)
    updateComponents  a FLAT list of components; children are referenced by id; one id is "root"
    updateDataModel   set a value at a JSON Pointer path; components bind to it with {"@path": ...}
    deleteSurface     remove the surface

and one renderer-to-agent message, ``action``, sent when the user clicks.

Structure (components) and data (data model) travel separately: that is
the idea that makes A2UI different from a plain JSON tree.

Validation uses the official JSON Schemas in ``schema/`` (copied from the
A2UI repository) plus the catalogs, so a message that passes here is a
message any conforming A2UI renderer accepts.
"""

from __future__ import annotations

import copy
import datetime as dt
import json
from functools import lru_cache
from pathlib import Path

SCHEMA = Path(__file__).parent / "schema"
VERSION = "1.0"
BASIC_CATALOG_ID = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json"
HTML_CATALOG_ID = "https://catalogs.genux.example/html/v1/catalog.json"
SPEC_BASE = "https://a2ui.org/specification/v1_0/"


# --------------------------------------------------------------- message builders
def create_surface(surface_id: str, catalog_id: str = BASIC_CATALOG_ID, components=None, data_model=None) -> dict:
    body = {"surfaceId": surface_id, "catalogId": catalog_id}
    if components is not None:
        body["components"] = components
    if data_model is not None:
        body["dataModel"] = data_model
    return {"version": VERSION, "createSurface": body}


def update_components(surface_id: str, components: list) -> dict:
    return {"version": VERSION, "updateComponents": {"surfaceId": surface_id, "components": components}}


def update_data_model(surface_id: str, path: str, value) -> dict:
    """value=None deletes the key (v1.0 makes value required; null means delete)."""
    return {"version": VERSION, "updateDataModel": {"surfaceId": surface_id, "path": path, "value": value}}


def delete_surface(surface_id: str) -> dict:
    return {"version": VERSION, "deleteSurface": {"surfaceId": surface_id}}


def message_kind(msg: dict) -> str | None:
    return next((k for k in ("createSurface", "updateComponents", "updateDataModel", "deleteSurface", "action") if k in msg), None)


# --------------------------------------------------------------- schema validation
def _load(name):
    return json.loads((SCHEMA / name).read_text(encoding="utf-8"))


@lru_cache(maxsize=None)
def _registry(with_html: bool):
    """Official schemas + one combined catalog under the placeholder URI the envelope expects."""
    from referencing import Registry, Resource

    common = _load("common_types.json")
    basic = _load("basic_catalog.json")
    combined = {
        "$schema": "https://json-schema.org/draft/2020-12/schema", "$id": SPEC_BASE + "catalog.json",
        "components": dict(basic["components"]), "functions": basic["functions"], "$defs": copy.deepcopy(basic["$defs"]),
    }
    if with_html:
        combined["components"].update(_load("genux_html_catalog.json")["components"])
    combined["$defs"]["anyComponent"] = {"oneOf": [{"$ref": f"#/components/{n}"} for n in combined["components"]]}
    resources = [
        (SPEC_BASE + "agent_to_renderer.json", _load("agent_to_renderer.json")),
        (SPEC_BASE + "renderer_to_agent.json", _load("renderer_to_agent.json")),
        (SPEC_BASE + "common_types.json", common),
        (SPEC_BASE + "catalog.json", combined),
    ]
    return Registry().with_resources([(uri, Resource.from_contents(doc)) for uri, doc in resources]), combined


def _validator(ref: str, with_html: bool):
    from jsonschema import Draft202012Validator

    registry, _ = _registry(with_html)
    return Draft202012Validator({"$ref": ref}, registry=registry)


def explain_component(comp: dict, with_html: bool = True) -> list[str]:
    """Precise, model-readable errors for one component (used for the correction loop)."""
    _, combined = _registry(with_html)
    cid, name = comp.get("id", "?"), comp.get("component")
    if name not in combined["components"]:
        return [f"component id={cid!r}: unknown component {name!r}; allowed: {', '.join(combined['components'])}"]
    errs = sorted(_validator(SPEC_BASE + f"catalog.json#/components/{name}", with_html).iter_errors(comp), key=lambda e: list(e.path))
    out = []
    for e in errs:
        where = "/".join(str(p) for p in e.path) or "(component)"
        msg = e.message if len(e.message) < 160 else e.message[:160] + "..."
        if e.validator == "oneOf" and isinstance(e.instance, dict) and "path" in e.instance:
            msg = 'a data binding must be {"@path": "/..."} in A2UI v1.0 (not {"path": ...})'
        out.append(f"component id={cid!r} ({name}) at {where}: {msg}")
    return out or [f"component id={cid!r} ({name}): has properties the catalog does not define"]


def validate_message(msg: dict, with_html: bool = False) -> list[str]:
    """Validate one agent-to-renderer message against the official schema + catalog(s)."""
    v = _validator(SPEC_BASE + "agent_to_renderer.json", with_html)
    if v.is_valid(msg):
        return []
    body = msg.get("updateComponents") or msg.get("createSurface") or {}
    comps = body.get("components") if isinstance(body, dict) else None
    if isinstance(comps, list):
        detailed = [e for c in comps if isinstance(c, dict) for e in (explain_component(c, with_html) if not _component_ok(c, with_html) else [])]
        if detailed:
            return detailed
    best = next(iter(sorted(v.iter_errors(msg), key=lambda e: -len(list(e.path)))), None)
    return [f"{message_kind(msg) or 'message'}: {best.message[:200]}" if best else "invalid message"]


def _component_ok(comp, with_html):
    _, combined = _registry(with_html)
    if comp.get("component") not in combined["components"]:
        return False
    schema = {"allOf": [{"$ref": SPEC_BASE + "common_types.json#/$defs/ComponentCommon"},
                        {"$ref": SPEC_BASE + f"catalog.json#/components/{comp['component']}"}], "unevaluatedProperties": False}
    from jsonschema import Draft202012Validator

    return Draft202012Validator(schema, registry=_registry(with_html)[0]).is_valid(comp)


def validate_action(msg: dict) -> list[str]:
    """Validate a renderer-to-agent message (a user action)."""
    v = _validator(SPEC_BASE + "renderer_to_agent.json", False)
    return [e.message[:200] for e in v.iter_errors(msg)]


def check_topology(components: list[dict]) -> list[str]:
    """Things JSON Schema cannot see: a root exists and every referenced id exists."""
    ids = {c.get("id") for c in components}
    errors = [] if "root" in ids else ['no component has id "root"']
    for c in components:
        refs = []
        if isinstance(c.get("child"), str):
            refs.append(c["child"])
        kids = c.get("children")
        if isinstance(kids, list):
            refs += kids
        elif isinstance(kids, dict):
            refs.append(kids.get("componentId"))
        errors += [f"component {c.get('id')!r} refers to missing id {r!r}" for r in refs if r not in ids]
    return errors


def validate_stream(messages: list[dict], with_html: bool = False) -> list[str]:
    errors = []
    comps: list[dict] = []
    for i, m in enumerate(messages):
        errors += [f"message {i + 1}: {e}" for e in validate_message(m, with_html)]
        body = m.get("createSurface") or m.get("updateComponents") or {}
        comps += body.get("components", []) if isinstance(body, dict) else []
    if comps:
        errors += check_topology(comps)
    return errors


def parse_jsonl(text: str) -> list[dict]:
    """Models emit one JSON message per line; tolerate blank lines and ``` fences."""
    out = []
    for line in text.splitlines():
        line = line.strip()
        if not line or line.startswith("```"):
            continue
        out.append(json.loads(line))
    return out


def now() -> str:
    return dt.datetime.now(dt.timezone.utc).isoformat(timespec="seconds").replace("+00:00", "Z")


def catalog_prompt(with_html: bool = False) -> str:
    """A compact system prompt generated from the official basic catalog (and ours)."""
    basic = _load("basic_catalog.json")
    lines = [
        "You generate A2UI v1.0 messages, one JSON object per line (JSONL), no prose, no fences.",
        'Every message has "version": "1.0". Start with createSurface, then updateComponents, then updateDataModel.',
        'Components are a FLAT list; children are referenced by id; exactly one component has id "root".',
        'Bind values with {"@path": "/json/pointer"}; inside a List template use relative paths like {"@path": "name"}.',
        'Text has variant "caption" or "body" only; write headings as Markdown ("## Title").',
        f"Default catalog: {BASIC_CATALOG_ID}. Components:",
    ]
    for name, d in basic["components"].items():
        props = dict(d.get("properties", {}))
        for part in d.get("allOf", []):
            props.update(part.get("properties", {}))
        lines.append(f"- {name}: " + ", ".join(k for k in props if k != "component"))
    if with_html:
        html = _load("genux_html_catalog.json")
        lines.append(f'Extra catalog {HTML_CATALOG_ID} (set "@catalogId" on the component): '
                     "HtmlFrame: title, html, caption, allowedEvents. " + html["instructions"])
    lines.append("Catalog guidelines: " + basic.get("instructions", "")[:600])
    return "\n".join(lines)


def official_check(messages: list[dict]):
    """Run the stream through Google's @a2ui/web_core MessageProcessor (Node).

    Returns the parsed result, or None when Node or node_modules are missing
    (run ``npm install`` in the repository root to enable it)."""
    import shutil
    import subprocess

    root = Path(__file__).resolve().parents[2]
    if not shutil.which("node") or not (root / "node_modules" / "@a2ui" / "web_core").exists():
        return None
    proc = subprocess.run(["node", str(Path(__file__).parent / "conformance.mjs")], input="\n".join(json.dumps(m) for m in messages),
                          capture_output=True, text=True, timeout=60)
    return json.loads(proc.stdout) if proc.stdout.strip() else {"ok": False, "errors": [proc.stderr[-500:]]}
