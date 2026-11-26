# Video 6 - Harness integration: generative UI inside the agent loop (≈12 min)

**Goal:** show that, inside a harness, generative UI is tool use: UI tools next to file tools, two surfaces, validation as feedback, and clicks as conversation turns.

| Time | On screen | Do | Say |
|---|---|---|---|
| 0:00 | `06_harness/README.md` | Flowchart | "Parts 1-5 were protocols and formats. Here they meet a coding-agent harness: the loop that calls tools until the model stops." |
| 0:45 | `shared/harness.py` | `Harness.run`, `Tool(ui=True)`, `Workspace` | "Every step emits an event; UI tools are tools whose result is drawn by surfaces. The workspace is a private copy the agent can't escape." |
| 1:45 | Terminal: `cd lab1_static && python agent.py` | Let it print | "Static: the agent lists and reads the CSVs, then calls show_metric/show_chart/show_table. Terminal surface: rich panels." |
| 2:30 | `python agent.py --web` (8061) | Open the page | "Same agent, second surface: the run bridged to AG-UI." |
| 3:00 | `agent.py`, `shared/surfaces.py` | README steps 1-6 | "The bridge: harness events → AG-UI events on a queue; the HTTP handler drains it while the loop runs in a thread." |
| 4:15 | lab2_declarative: `python agent.py` | Read the "! render_ui failed" line | "Declarative: render_ui validates. The first spec has a PieChart and a 7/5 chart; the error goes back as a tool result; the model fixes it. No retry code - just the loop." |
| 5:00 | `agent.py` `render_ui`, `harness.py` `ok` | Steps 1-4 | — |
| 6:00 | `--web` (8062) | Point at the red "rejected" chip | "Only the valid spec reached the page." |
| 6:30 | lab3_open_ended: `python agent.py`, then `--web` (8063) | Open `artifacts/break-even-calculator.html` in the editor | "Open-ended: render_html. Policy first, artifact saved with its own CSP, sandboxed in the browser; the terminal just points at the file." |
| 7:30 | `agent.py`, `surfaces.py` panel, `web/harness.js` | Steps 1-4 | — |
| 8:30 | lab4_mixed: `python agent.py` (8064) | Click Reorder, then the calculator's "Use this price" | "Mixed and conversational: each click becomes the next user turn. The agent places a real order - inventory.json changes - and patches the UI with update_ui, which re-validates." |
| 9:30 | `shared/web.py`, `agent.py` `UiState`, `harness.js` `paintChanged` | Steps 1-4 | "Clicks are requests, not commands: allow-listed, and the agent decides which tools to call." |
| 10:45 | Terminal | `python demo.py`, `python -m pytest test_lab.py` | Read "user turns: [...]" and the inventory.json line. |
| 11:15 | Root README + `evidence/TEST_REPORT.md` | — | "All 24 labs: tests, recorded demos, screenshots, and official-library conformance checks. Thanks for watching." |
