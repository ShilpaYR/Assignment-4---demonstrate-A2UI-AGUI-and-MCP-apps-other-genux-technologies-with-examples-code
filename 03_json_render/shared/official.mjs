// Check a spec (or a SpecStream of JSONL patches) with the official json-render library.
//   node official.mjs <base|hybrid|html> < spec.json         -> {"ok", "issues", "spec"}
//   node official.mjs <base|hybrid|html> --stream < patches.jsonl
// --stream compiles the patches with @json-render/core's compileSpecStream first,
// so the Python patch application can be compared with the library's.
import { readFileSync } from "node:fs";
import { compileSpecStream, validateSpec } from "@json-render/core";
import { CATALOGS } from "./catalog.mjs";

const [name = "base", mode] = process.argv.slice(2);
const text = readFileSync(0, "utf8");
const spec = mode === "--stream" ? compileSpecStream(text) : JSON.parse(text);
const structural = validateSpec(spec);                 // dangling children, missing root, ...
const issues = [...structural.issues.filter((i) => i.severity === "error").map((i) => i.message)];
// Component names and props: parse each element's props with ITS OWN component's Zod schema from the
// catalog. (catalog.validate() parses props against the union of all components - a Row's empty schema
// accepts anything - and it does not skip render-time expressions such as {"$state": ...}.)
const isExpr = (v) => v && typeof v === "object" && !Array.isArray(v) && Object.keys(v).some((k) => k.startsWith("$"));
for (const [id, el] of Object.entries(spec.elements ?? {})) {
  const def = CATALOGS[name].data.components[el.type];
  if (!def) { issues.push(`${id}: unknown component ${el.type}; allowed: ${CATALOGS[name].componentNames.join(", ")}`); continue; }
  const props = Object.fromEntries(Object.entries(el.props ?? {}).filter(([, v]) => !isExpr(v)));
  for (const [k, sub] of Object.entries(def.props.shape)) if (!(k in props) && (sub.safeParse(null).success || isExpr(el.props?.[k]))) props[k] = sub.safeParse(null).success ? null : undefined;
  const r = def.props.partial(Object.fromEntries(Object.keys(el.props ?? {}).filter((k) => isExpr(el.props[k])).map((k) => [k, true]))).safeParse(props);
  if (!r.success) issues.push(...r.error.issues.map((e) => `${id} (${el.type}) ${e.path.join("/")}: ${e.message}`));
}
console.log(JSON.stringify({ ok: issues.length === 0, issues, spec }));
