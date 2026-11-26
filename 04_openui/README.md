# Part 4 - OpenUI Lang: a compact, line-oriented UI language

**OpenUI Lang** (thesys, `@openuidev/lang-core`, MIT) is a small language for model-generated UI. A program is one statement per line:

```text
root = Stack([dash])
dash = Card("Campus Coffee Cart - this week", [kpis, chart, items, stock])
kpis = Row([rev, cups, ticket])
rev = Metric("Revenue", "$4,669.20", "+8.4%")
```

Arguments are **positional** (the order of the component's Zod keys), and a name may be used **before** it is defined (forward references / hoisting). There are no closing braces to wait for, so a program renders while it streams, and it is markedly shorter than JSON for the same UI (lab 2 measures it with the o200k tokenizer).

Everything in this part uses the **official parser**: in Node for validation (`shared/parse.mjs`) and in the browser, bundled with esbuild into [`shared/web/vendor/openui-lang-core.js`](shared/web/vendor/). The libraries live in [`shared/library.mjs`](shared/library.mjs); `node shared/build.mjs` generates each library's own prompt (`library.prompt()`), its parser schema (`library.toJSONSchema()`) and the browser bundle.

| Lab | Mode | Library | Highlight |
|---|---|---|---|
| [lab1_static](lab1_static/) | static | `SalesDashboard`, `InventoryCard` (pre-built) | the model can only pick and fill; the page owns the look |
| [lab2_declarative](lab2_declarative/) | declarative | primitives | forward references while streaming; token comparison vs JSON formats |
| [lab3_open_ended](lab3_open_ended/) | open-ended | `HtmlArtifact` only | the document is "partial" until its string closes; mounted only when complete |
| [lab4_mixed](lab4_mixed/) | mixed | primitives + `HtmlArtifact` | user events answered with **edits** (`mergeStatements`); the artifact is 70% of the token budget |

**Edits are statements.** OpenUI's edit model is unusually simple: to change one element, send its line again (`ticket = Metric("Avg ticket", "$4.20", "new list price")`); `mergeStatements(program, patch)` replaces it and keeps the rest.

Note: `@openuidev/lang-core` sends pseudonymous install telemetry during `npm install` (see its README); set your npm/CI policy accordingly.

Video script: [docs/video-scripts/part4_openui.md](../docs/video-scripts/part4_openui.md).
