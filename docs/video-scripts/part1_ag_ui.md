# Video 1 - AG-UI: the event stream between agent and page (≈13 min)

**Goal of the video:** show that AG-UI is a transport of typed events, and that the same transport carries all four generation modes.

| Time | On screen | Do | Say (key points) |
|---|---|---|---|
| 0:00 | Root `README.md`, mode × technology table | Scroll to the matrix | "Assignment 4: six technologies, four modes each. One scenario everywhere: a campus coffee cart dashboard. Part 1 is AG-UI." |
| 0:40 | `01_ag_ui/README.md` (preview) | Show the sequence diagram | "AG-UI defines ~20 event types over SSE. The page sends RunAgentInput, the agent streams events. It says nothing about what a UI looks like - that's the mode." |
| 1:30 | Terminal | `cd 01_ag_ui/lab1_static && python server.py`, open http://127.0.0.1:8011 | "Static mode: three components exist in the page already." Point at the wire panel: TOOL_CALL_START / ARGS / END. |
| 2:30 | `server.py` | README steps 1-4: `TOOLS`, `check_args`, the `run()` generator, `RunAgentInput.model_validate` + `EventEncoder` | "Components are offered as function-calling tools. The server checks every call before it leaves." |
| 3:30 | `page/app.js` | Steps 5-6: `RENDERERS`, the `TOOL_CALL_END` case | "This table *is* static generative UI." |
| 4:00 | Terminal | `python demo.py`, then `python -m pytest test_lab.py` | Read the event counts line. |
| 4:30 | lab2_declarative in the browser (port 8012) | Click "Run agent" twice; watch the skeleton | "Declarative: the model writes a layout from a catalog. AG-UI carries it as shared state: one snapshot, then one JSON Patch per element." |
| 5:15 | `server.py`, `common/catalog.py`, `page/app.js` | Steps 1-6 | "Prompt and validator are generated from one catalog. Invalid layouts become RUN_ERROR. The page: snapshot replaces, delta patches." |
| 7:00 | Terminal | `python demo.py` (shows the deltas), pytest | Mention `test_invalid_layout_becomes_run_error`. |
| 7:30 | lab3_open_ended (port 8013) | Watch the HTML stream, then move a slider, click "Use this price" | "Open-ended: no catalog. The HTML streams as text but runs only after the policy check, in a sandboxed iframe." Point at "iframe -> page: apply_price". |
| 8:15 | `server.py`, `common/sandbox.py`, `common/web/sandbox.js` | Steps 1-6 | "Three layers: policy, CSP first in head, sandbox without allow-same-origin. One message shape, one allowed event." |
| 9:30 | Terminal | `python demo.py` | Read the token table: static < declarative < open-ended. |
| 10:00 | lab4_mixed (port 8014) | Click Reorder → Approve; move the calculator slider → "Use this price" | "Mixed: catalog + one sandboxed region, and three round trips: a Button action, a client tool with a human confirmation, and an event from the sandbox." |
| 10:45 | `server.py` `route()`, `page/app.js` `TOOLS` + `confirmDialog` + `paintChanged` | Steps 1-6 | "The page declares `confirm_restock`; the agent calls it; the answer returns as a tool message. Only touched elements re-render, so the iframe keeps its state." |
| 12:15 | Terminal | `python demo.py` (5 runs), pytest | Point at run 5: unknown action → RUN_ERROR. |
| 12:45 | Part README table | — | "Next: A2UI - a format where structure and data travel separately." |
