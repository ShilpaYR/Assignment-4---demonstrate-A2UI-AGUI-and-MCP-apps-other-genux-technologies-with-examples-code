// Generate the prompts and JSON Schemas from the catalogs: `node build.mjs` (or `npm run build:json-render`).
import { writeFileSync } from "node:fs";
import { z } from "zod";
import { CATALOGS } from "./catalog.mjs";

const RULES = {
  base: ["Use short element ids such as kpi-rev or chart-1.", "Fill every prop; use null for an optional prop you do not need."],
  hybrid: ["Use HtmlBlock at most once, only for the interactive what-if price calculator.",
    "Give the HtmlBlock on.apply_price = {\"action\": \"apply_price\"}.", "Use short element ids."],
  html: ["Reply with a root HtmlBlock only; the document must be self-contained (inline CSS/JS, no network)."],
};
for (const [name, cat] of Object.entries(CATALOGS)) {
  writeFileSync(new URL(`./generated/prompt_${name}.txt`, import.meta.url),
    cat.prompt({ system: "You build UIs for a coffee-cart analytics app.", customRules: RULES[name] }));
  // the spec shape from the library + one JSON Schema per component's Zod props (for the Python validator)
  const props = Object.fromEntries(Object.entries(cat.data.components).map(([n, c]) => [n, z.toJSONSchema(c.props)]));
  const doc = { spec: cat.jsonSchema(), props, actions: cat.actionNames, builtinActions: ["setState", "pushState", "removeState", "validateForm"] };
  writeFileSync(new URL(`./generated/schema_${name}.json`, import.meta.url), JSON.stringify(doc, null, 2));
  console.log(`generated/prompt_${name}.txt, generated/schema_${name}.json  (${cat.componentNames.length} components)`);
}
