// Generate prompts + parser schemas from the libraries, and bundle the official parser for the browser.
//   node build.mjs
import { writeFileSync } from "node:fs";
import { build } from "esbuild";
import { LIBRARIES } from "./library.mjs";

for (const [name, lib] of Object.entries(LIBRARIES)) {
  writeFileSync(new URL(`./generated/prompt_${name}.txt`, import.meta.url), lib.prompt());
  writeFileSync(new URL(`./generated/schema_${name}.json`, import.meta.url), JSON.stringify(lib.toJSONSchema(), null, 2));
  console.log(`generated/prompt_${name}.txt, generated/schema_${name}.json`);
}
await build({
  entryPoints: [new URL("./vendor-entry.mjs", import.meta.url).pathname], bundle: true, format: "esm", minify: true,
  outfile: new URL("./web/vendor/openui-lang-core.js", import.meta.url).pathname, logLevel: "warning",
  banner: { js: "// @openuidev/lang-core (MIT, https://github.com/thesysdev/openui), bundled by 04_openui/shared/build.mjs" },
});
console.log("web/vendor/openui-lang-core.js (official parser, bundled for the browser)");
