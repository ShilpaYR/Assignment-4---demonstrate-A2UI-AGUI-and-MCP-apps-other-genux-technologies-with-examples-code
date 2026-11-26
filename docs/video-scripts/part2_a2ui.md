# Video 2 - A2UI v1.0: structure and data as two streams (≈13 min)

**Goal:** show A2UI's four messages, data binding, catalogs, and that every stream passes the official schema *and* Google's own renderer core.

Before recording: `npm install` in the repo root (enables the `@a2ui/web_core` check).

| Time | On screen | Do | Say |
|---|---|---|---|
| 0:00 | `02_a2ui/README.md` | Ideas table | "A2UI is a declarative format from Google, current version 1.0. Four agent-to-renderer messages; components bind to a data model with `@path`; catalogs can be mixed per component." |
| 1:00 | `shared/schema/` + `NOTICE.md` | — | "These are the official v1.0 schemas, copied unchanged. Three checks run on every stream: Python jsonschema, Google's web_core processor, and our renderer." |
| 1:30 | lab1_static (8021) | Run; click Reorder | "Static: the developer wrote the surface; the agent only fills the data model." Wire: createSurface with components, then three updateDataModel. |
| 2:15 | `shared/dashboard.py`, `server.py`, `shared/web/surface.js` | README steps 1-6 | Show `{"@path": ...}`, the List template with relative paths, `formatString`, `refresh()` updating only bound nodes, the `action` message. |
| 4:00 | Terminal | `python demo.py` | Point at "official renderer core (@a2ui/web_core): accepted". |
| 4:30 | lab2_declarative (8022) | Run; watch the wire: attempt 1 INVALID, attempt 2 valid; fill the form, Place order | "Declarative: the model writes the whole JSONL stream. Validation errors are results - they go back to the model." |
| 5:15 | `server.py` `generate()`, `shared/a2ui.py` `explain_component`, `surface.js` TextField | Steps 1-6 | "The two errors are real v0.9 habits: variant h2 and `path` without `@`. Two-way binding keeps form values in the data model until the action." |
| 7:00 | Terminal | `python demo.py`; optionally `node ../shared/conformance.mjs fixtures/attempt1.jsonl` | "Google's processor rejects attempt 1 for the same reason." |
| 7:45 | lab3_open_ended (8023) | Move slider, "Use this price" | "Open-ended in A2UI means a custom catalog. Our catalog has one component, HtmlFrame." |
| 8:15 | `shared/schema/genux_html_catalog.json`, `server.py`, `surface.js` catalog resolution | Steps 1-5 | "Without the custom catalog the message is invalid; a renderer that doesn't know it shows 'catalog not supported' - opt-in on both sides." |
| 9:45 | lab4_mixed (8024) | Calculator → "Use this price"; Reorder; Close dashboard | "Mixed: basic catalog plus one HtmlFrame with @catalogId on the same surface. The agent uses all four message types - the receipt is an updateComponents, Close is deleteSurface." |
| 10:30 | `shared/dashboard.py` (HtmlFrame), `server.py` `handle_action`, `surface.js` targeted re-render | Steps 1-5 | "Only the frame may send apply_price. The calculator keeps its slider after the receipt appears." |
| 12:00 | Terminal | `python demo.py`, `python -m pytest test_lab.py` | Read "after restock the frame kept its slider at: $4.10". |
| 12:40 | Part README | — | "Next: json-render - one catalog that is prompt, validator and registry." |
