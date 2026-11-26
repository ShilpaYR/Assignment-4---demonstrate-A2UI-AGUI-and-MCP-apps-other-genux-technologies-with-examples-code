# Video 3 - json-render: one catalog, a streaming spec, many renderers (≈12 min)

**Goal:** show the catalog defined with the official library, SpecStream, state/expressions/actions, and the same spec in a second renderer.

Before recording: `npm install && npm run build`.

| Time | On screen | Do | Say |
|---|---|---|---|
| 0:00 | `03_json_render/README.md` | Spec example | "json-render from Vercel Labs: a flat spec, state with `$state` expressions, `on` bindings for actions, and SpecStream - JSONL patches - for generation." |
| 0:45 | `shared/catalog.mjs`, `shared/build.mjs`, `shared/generated/prompt_base.txt` | Run `node shared/build.mjs` | "One Zod catalog → the library's own 16 KB prompt, and per-component JSON Schemas for the Python servers." |
| 1:45 | lab1_static (8031) | Run; "Hide top items"; Reorder | "Static: the developer wrote every element; values are `$state` expressions; the agent only writes `/state`." Wire: `setState (local)` never hits the server. |
| 2:30 | `shared/specs.py`, `server.py`, `shared/web/jr-render.js` | README steps 1-6 | `$cond`, `visible`, built-in vs custom actions, dependency tracking. |
| 4:00 | Terminal | `python demo.py` | "@json-render/core validateSpec + catalog props: valid". |
| 4:30 | lab2_declarative (8032) | Run; read the status line | "Declarative: the model streams SpecStream. Each line is validated on arrival; the hallucinated PieChart line is dropped, the rest renders." |
| 5:15 | `server.py` `lines()` + `stream()`, `shared/jr.py` | Steps 3-6 | "First paint after the first element patch, long before the end." |
| 6:30 | Terminal | `python demo.py` | "The official compileSpecStream on the raw output flags PieChart; on the accepted patches it's valid and identical to the Python result." |
| 7:00 | lab3_open_ended (8033) | Slider + "Use this price" | "Open-ended: a catalog with one component, HtmlBlock. The `on` map is the sandbox allow-list; the caption is state." |
| 7:45 | `catalog.mjs` HtmlBlock, `specs.py` `html_spec`, `jr-render.js` `htmlBlock()` | Steps 1-5 | — |
| 8:45 | lab4_mixed (8034) | Calculator → "Use this price", Hide top items, Reorder; scroll to the terminal view | "Mixed: hybrid catalog. Three behaviours in one spec. And below: the same spec rendered by a terminal renderer." |
| 9:30 | `server.py` (`/jr/terminal`), `shared/terminal.py` | Steps 1-5 | "The HtmlBlock degrades to a placeholder; every catalog component survives. setState is page-local, so the terminal still shows the table." |
| 11:00 | Terminal | `python demo.py`, pytest | Show the rich panel output. |
| 11:40 | Part README | — | "Next: OpenUI Lang - a language instead of JSON." |
