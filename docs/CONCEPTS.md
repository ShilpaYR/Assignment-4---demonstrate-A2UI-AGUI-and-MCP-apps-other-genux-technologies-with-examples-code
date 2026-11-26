# Generative UI concepts used in this repository

## Two independent decisions

1. **What may the model generate?** - the *mode*:

| Mode | The model decides | The application decides | Cost / risk |
|---|---|---|---|
| **Static** | which pre-built component to show, and its data | every component, its look and behaviour | lowest tokens, fully predictable, limited to what was built |
| **Declarative** | the layout, from a catalog of allowed components | the catalog (names, props, actions), validation, rendering | moderate tokens; safe as long as the catalog is enforced |
| **Open-ended** | everything: HTML/CSS/JS | only the sandbox and the policy around it | most tokens; untrusted code; maximum flexibility |
| **Mixed (hybrid)** | a catalog layout + one sandboxed region | the catalog, the one escape hatch, the policy | the recommended default: predictable almost everywhere, free where it must be |

2. **How does the UI reach the user?** - the *carrier*: an event stream into your own app (AG-UI), a format any renderer can draw (A2UI, json-render, OpenUI Lang), an app embedded in someone else's host (MCP Apps), or the tool loop of an agent harness. These are separate choices; Parts 1-6 combine each carrier with all four modes.

## The same four modes in six technologies

| | Static | Declarative | Open-ended | Mixed |
|---|---|---|---|---|
| **AG-UI** (Part 1) | `TOOL_CALL_*` → pre-built renderer per tool | catalog spec as `STATE_SNAPSHOT` + `STATE_DELTA` | HTML streamed as text, delivered as `ACTIVITY_SNAPSHOT` | state with `GeneratedView` + client tool (human in the loop) |
| **A2UI v1.0** (Part 2) | developer's surface, agent sends `updateDataModel` | model writes `createSurface`/`updateComponents`, corrected on schema errors | custom catalog with one `HtmlFrame` | basic catalog + `HtmlFrame` via `@catalogId`, all four message types |
| **json-render** (Part 3) | template spec with `$state`, agent writes `/state` | SpecStream validated line by line | catalog of only `HtmlBlock` | hybrid catalog, `setState` vs server actions, terminal renderer |
| **OpenUI Lang** (Part 4) | library of pre-built composites | primitives, forward references while streaming | `HtmlArtifact` only | primitives + `HtmlArtifact`, edits via `mergeStatements` |
| **MCP Apps** (Part 5) | pre-built view for `structuredContent` | generic catalog-renderer view | generated HTML in a nested sandbox | catalog + generated region, app-only tools, text-only host |
| **Harness** (Part 6) | `show_*` UI tools next to file tools | `render_ui` validated, loop self-corrects | `render_html` → artifact + sandbox | hybrid `render_ui` + `update_ui`, clicks become turns |

## How each technology updates a UI after the first render

| Technology | Update unit |
|---|---|
| AG-UI | `STATE_DELTA` - RFC 6902 JSON Patch on shared state |
| A2UI | `updateDataModel` (a value at a JSON Pointer) or `updateComponents` (replace components by id) |
| json-render | SpecStream patches, usually on `/state` |
| OpenUI Lang | a replacement statement, merged with `mergeStatements` |
| MCP Apps | whatever the app's own tools return (here: JSON Patch in `structuredContent`) |
| Harness | an `update_ui(ops)` tool call, re-validated before it is shown |

## Safety model for model-written HTML (open-ended and mixed)

Three independent layers, used in every lab that runs generated HTML:

1. **Policy check** before sending (`common/sandbox.py`): size limit; no `<script src>`, external CSS, `fetch`/`XMLHttpRequest`/`WebSocket`/`EventSource`, nested frames, remote images.
2. **Content-Security-Policy** injected as the first element of `<head>`: `default-src 'none'`, inline script/style only, `connect-src 'none'`.
3. **Sandboxed iframe** - `sandbox="allow-scripts"` without `allow-same-origin` - so the document runs in an opaque origin. Its only way out is `postMessage` with one accepted shape, from that exact frame, with an allow-listed event name; the server re-validates the payload.

A sandbox reduces capabilities; it does not make arbitrary output trustworthy. Events from generated regions are always treated as untrusted input.

## Validation is part of the loop

Each lab validates model output against the contract *before* it reaches a renderer, and treats errors as information:

- A2UI lab 2 and Harness lab 2 send readable validation errors back to the model, which corrects itself;
- json-render lab 2 drops a single invalid SpecStream line and keeps the rest;
- every A2UI stream is accepted by Google's own `@a2ui/web_core` processor; every json-render spec by `@json-render/core`; every OpenUI program by the official parser; every MCP Apps bridge message by the `@modelcontextprotocol/ext-apps` schemas.

## Measuring cost

Token counts use the o200k_base tokenizer (`gpt-tokenizer` from npm, or `tiktoken`); if neither is available, demos print "estimate: characters / 4". Recorded comparisons:

- Part 1 lab 3: the same coffee-cart data as static tool calls vs a declarative spec vs one open-ended HTML widget;
- Part 4 lab 2: the same dashboard as OpenUI Lang vs json-render flat spec vs SpecStream vs a nested JSON tree;
- Part 4 lab 4: the share of the answer taken by the single `HtmlArtifact`.

These are measurements of this repository's samples, not general laws.

## Offline vs live

Every lab's model calls go through `common/llm.py`. By default `ScriptedLLM` replays the lab's `fixtures/` (authored by `tools/make_fixtures.py` from one canonical scenario), so tests and demos are reproducible and free. With `GENUX_LIVE=1` and `API_KEY` (or `OPENAI_API_KEY`) set, `LiveLLM` calls any OpenAI-compatible endpoint (`BASE_URL`, `MODEL`, default `gpt-4.1-mini`) with the *same* prompts, validation and renderers. The recorded outputs in this repository come from scripted mode.
