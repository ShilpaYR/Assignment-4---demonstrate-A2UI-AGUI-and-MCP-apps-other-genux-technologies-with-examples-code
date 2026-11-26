"""RFC 6901 JSON Pointer + the RFC 6902 operations the labs use (add, replace, remove, test).

AG-UI's STATE_DELTA, json-render's SpecStream and A2UI's data-model paths
all use JSON Pointer, so one small implementation serves all of them.
The browser twin is ``common/web/jsonpatch.js``.
"""

from __future__ import annotations

import copy


def _tokens(pointer: str) -> list[str]:
    if pointer in ("", "/"):
        return []
    if not pointer.startswith("/"):
        raise ValueError(f"bad JSON pointer {pointer!r}")
    return [t.replace("~1", "/").replace("~0", "~") for t in pointer[1:].split("/")]


def get(doc, pointer: str):
    cur = doc
    for t in _tokens(pointer):
        cur = cur[int(t)] if isinstance(cur, list) else cur[t]
    return cur


def _parent(doc, pointer: str):
    toks = _tokens(pointer)
    if not toks:
        return None, None
    cur = doc
    for t in toks[:-1]:
        if isinstance(cur, list):
            cur = cur[int(t)]
        else:
            cur = cur.setdefault(t, {})
    return cur, toks[-1]


def set_value(doc, pointer: str, value):
    """Set (creating intermediate objects) - the A2UI updateDataModel behaviour."""
    parent, key = _parent(doc, pointer)
    if parent is None:
        return copy.deepcopy(value)
    if isinstance(parent, list):
        idx = len(parent) if key == "-" else int(key)
        if idx == len(parent):
            parent.append(value)
        else:
            parent[idx] = value
    else:
        parent[key] = value
    return doc


def apply(doc, ops: list[dict]):
    """Apply operations in order and return the new document (input is not mutated)."""
    doc = copy.deepcopy(doc)
    for op in ops:
        kind, path = op["op"], op["path"]
        if kind in ("add", "replace"):
            parent, key = _parent(doc, path)
            if parent is None:
                doc = copy.deepcopy(op["value"])
            elif isinstance(parent, list):
                idx = len(parent) if key == "-" else int(key)
                if kind == "add":
                    parent.insert(idx, copy.deepcopy(op["value"]))
                else:
                    parent[idx] = copy.deepcopy(op["value"])
            else:
                if kind == "replace" and key not in parent:
                    raise KeyError(f"replace target {path} does not exist")
                parent[key] = copy.deepcopy(op["value"])
        elif kind == "remove":
            parent, key = _parent(doc, path)
            if isinstance(parent, list):
                del parent[int(key)]
            else:
                del parent[key]
        elif kind == "test":
            if get(doc, path) != op["value"]:
                raise ValueError(f"test failed at {path}")
        else:
            raise ValueError(f"unsupported op {kind!r}")
    return doc
