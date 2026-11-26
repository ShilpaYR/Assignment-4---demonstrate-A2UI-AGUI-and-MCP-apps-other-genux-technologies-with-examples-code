// Parse an OpenUI Lang program with the OFFICIAL parser and print the result as JSON.
//   node parse.mjs <static|declarative|html|hybrid> < program.oui
import { readFileSync } from "node:fs";
import { createParser } from "@openuidev/lang-core";
import { LIBRARIES } from "./library.mjs";

const name = process.argv[2] ?? "declarative";
const result = createParser(LIBRARIES[name].toJSONSchema(), "Stack").parse(readFileSync(0, "utf8"));
const count = (n) => (n && typeof n === "object" ? (n.type === "element" ? 1 : 0) + Object.values(n.props ?? n).flat().reduce((a, v) => a + count(v), 0) : 0);
console.log(JSON.stringify({ ok: result.meta.errors.length === 0 && result.meta.unresolved.length === 0, meta: result.meta, elements: count(result.root), root: result.root }));
