# Part 3 - json-render: one catalog, a streaming spec, many renderers

**json-render** (Vercel Labs, `@json-render/core` + renderers for React, terminal and more) describes a UI as a flat **spec**:

```json
{"root": "dash",
 "elements": {"dash": {"type": "Card", "props": {"title": "..."}, "children": ["m-rev"]},
              "m-rev": {"type": "Metric", "props": {"label": "Revenue", "value": {"$state": "/kpis/revenue"}}, "children": [],
                        "on": {"press": {"action": "restock_beans", "params": {"kg": 10}}}}},
 "state": {"kpis": {"revenue": "$4,669.20"}}}
```

Its core promise: **the catalog is the prompt, the validator and the renderer registry at once.** Here the catalogs are defined with the official library in [`shared/catalog.mjs`](shared/catalog.mjs) (Zod props). `node shared/build.mjs` exports from them the library's own system prompt (`catalog.prompt()`, ~16 KB) and one JSON Schema per component for the Python servers. Models stream specs as **SpecStream**: JSONL, one RFC 6902 patch per line.

| Lab | Mode | Catalog | What the model writes |
|---|---|---|---|
| [lab1_static](lab1_static/) | static | base | only `/state` (via `fill_state`); the developer wrote every element with `$state` bindings |
| [lab2_declarative](lab2_declarative/) | declarative | base | the whole spec as SpecStream, validated line by line (a hallucinated `PieChart` is dropped) |
| [lab3_open_ended](lab3_open_ended/) | open-ended | `htmlCatalog` = only `HtmlBlock` | one element holding a whole HTML document |
| [lab4_mixed](lab4_mixed/) | mixed | `hybridCatalog` = base + `HtmlBlock` | catalog components + one HtmlBlock + state; also rendered in a terminal |

**Pieces in `shared/`**

| File | Role |
|---|---|
| `catalog.mjs`, `build.mjs` | official catalogs; generate `generated/prompt_*.txt` and `generated/schema_*.json` |
| `official.mjs` | validates a spec or SpecStream with `@json-render/core` (`compileSpecStream`, `validateSpec`, each component's Zod schema) |
| `jr.py` | Python validation from the exported schemas; SpecStream application; `official_check()` bridge to Node |
| `web/jr-render.js` | a DOM renderer: `$state`, `$bindState`, `$cond`, `visible`, `on` bindings, built-in `setState`, dependency-tracked re-render |
| `terminal.py` | a second renderer for the same spec, using `rich` |
| `specs.py` | the coffee-cart spec builders used for the template and the fixtures |

Video script: [docs/video-scripts/part3_json_render.md](../docs/video-scripts/part3_json_render.md).
