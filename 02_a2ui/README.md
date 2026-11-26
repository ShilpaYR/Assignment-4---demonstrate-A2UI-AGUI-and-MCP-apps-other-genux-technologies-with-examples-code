# Part 2 - A2UI: structure and data as two streams

**A2UI** (Agent-to-User Interface, from Google) is a *declarative UI format*, not a transport. An agent sends JSON messages that describe a **surface**; a renderer draws them with its own native components from a **catalog**. This part targets **A2UI v1.0**, the current stable version (Nov 2026), and validates every message against the official v1.0 JSON Schemas copied into [`shared/schema/`](shared/schema/) (Apache-2.0, see the NOTICE).

The ideas that make A2UI different:

| Idea | What it means | Where you see it |
|---|---|---|
| Four agent→renderer messages | `createSurface`, `updateComponents`, `updateDataModel`, `deleteSurface` | all labs; lab 4 uses all four |
| Flat component list | children are ids, one component is `root`; a child may arrive later | lab 2 streams components in batches |
| Structure ≠ data | components bind to a data model with `{"@path": "/kpis/revenue"}` | lab 1: developer writes structure, agent writes data |
| Templates | `List.children = {"componentId": "item_row", "path": "/items"}` with relative paths | every dashboard's "Top items" |
| Two-way binding + actions | inputs write into the data model; a Button's `action` carries bound values to the agent | lab 2's order form |
| Catalogs, mixable per component | `catalogId` on the surface, `@catalogId` on a component (new in v1.0) | lab 3 (custom catalog), lab 4 (basic + custom) |

| Lab | Mode | Who writes what |
|---|---|---|
| [lab1_static](lab1_static/) | static | developer writes the surface; the agent fills `fill_dashboard()` → `updateDataModel` |
| [lab2_declarative](lab2_declarative/) | declarative | the agent writes the whole JSONL stream; invalid output is sent back with errors and retried |
| [lab3_open_ended](lab3_open_ended/) | open-ended | a **custom catalog** with one `HtmlFrame`: the whole surface is model-written HTML in a sandbox |
| [lab4_mixed](lab4_mixed/) | mixed | basic catalog + one `HtmlFrame` (`@catalogId`) on the same surface; actions answered with all four message types |

**Three independent checks** run on every stream:
1. `shared/a2ui.py` - Python `jsonschema` against the official `agent_to_renderer.json` + catalogs, with readable per-component errors;
2. `shared/conformance.mjs` - Google's own renderer core, **`@a2ui/web_core` `MessageProcessor`**, in strict mode (needs `npm install` in the repo root);
3. `shared/web/surface.js` - this course's 200-line browser renderer, which draws the surface.

Transport here is plain SSE (`POST /a2ui/stream`, one A2UI message per event) and `POST /a2ui/action` for renderer→agent actions. A2UI is transport-agnostic: the same messages can ride inside AG-UI `CUSTOM` events, A2A or MCP.

Video script: [docs/video-scripts/part2_a2ui.md](../docs/video-scripts/part2_a2ui.md).
