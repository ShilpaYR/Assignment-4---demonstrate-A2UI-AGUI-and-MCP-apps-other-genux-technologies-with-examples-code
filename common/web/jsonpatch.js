// JSON Pointer (RFC 6901) and the JSON Patch (RFC 6902) operations the labs use.
// Twin of common/jsonpatch.py.
const tokens = (ptr) => (ptr === "" || ptr === "/" ? [] : ptr.slice(1).split("/").map((t) => t.replace(/~1/g, "/").replace(/~0/g, "~")));

export function getPointer(doc, ptr) {
  let cur = doc;
  for (const t of tokens(ptr)) { if (cur == null) return undefined; cur = cur[Array.isArray(cur) ? Number(t) : t]; }
  return cur;
}

export function setPointer(doc, ptr, value) {
  const toks = tokens(ptr);
  if (!toks.length) return structuredClone(value);
  let cur = doc;
  for (const t of toks.slice(0, -1)) { if (cur[t] === undefined || cur[t] === null) cur[t] = {}; cur = cur[t]; }
  const last = toks.at(-1);
  if (Array.isArray(cur) && last === "-") cur.push(value); else cur[last] = value;
  return doc;
}

export function applyPatch(doc, ops) {
  let out = structuredClone(doc ?? {});
  for (const op of ops) {
    const toks = tokens(op.path);
    if (!toks.length) { if (op.op === "add" || op.op === "replace") out = structuredClone(op.value); continue; }
    let parent = out;
    for (const t of toks.slice(0, -1)) { if (parent[t] === undefined) parent[t] = {}; parent = parent[t]; }
    const key = toks.at(-1);
    if (op.op === "add" || op.op === "replace") {
      if (Array.isArray(parent)) {
        const i = key === "-" ? parent.length : Number(key);
        op.op === "add" ? parent.splice(i, 0, structuredClone(op.value)) : (parent[i] = structuredClone(op.value));
      } else parent[key] = structuredClone(op.value);
    } else if (op.op === "remove") {
      Array.isArray(parent) ? parent.splice(Number(key), 1) : delete parent[key];
    } else if (op.op === "test") {
      if (JSON.stringify(getPointer(out, op.path)) !== JSON.stringify(op.value)) throw new Error(`test failed at ${op.path}`);
    } else throw new Error(`unsupported op ${op.op}`);
  }
  return out;
}
