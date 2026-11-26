# Assignment 4 - requirements coverage

Assignment: *"Demonstrate A2UI, AG-UI, MCP Apps and other GenUX technologies with example code. Progressively explain each example of a2ui, agui, mcp apps, json render, openui, harness integration - all the three modes for each - static, declarative and open-ended ux and mixed mode - with full code walkthrough of all the codelabs, showing execution of the code. All deliverables in a GitHub repo with a YouTube video for each part."* (500 points, submitted as a website URL)

## Coverage

| # | Requirement | Where | Status |
|---|---|---|---|
| 1 | A2UI examples, all modes | [`02_a2ui/`](02_a2ui/) - 4 labs, A2UI v1.0, official schemas + `@a2ui/web_core` check | ✅ |
| 2 | AG-UI examples, all modes | [`01_ag_ui/`](01_ag_ui/) - 4 labs, official `ag-ui-protocol` SDK | ✅ |
| 3 | MCP Apps examples, all modes | [`05_mcp_apps/`](05_mcp_apps/) - 4 labs, MCP Python SDK v2, a host, `ext-apps` schema check | ✅ |
| 4 | json-render examples, all modes | [`03_json_render/`](03_json_render/) - 4 labs, `@json-render/core` | ✅ |
| 5 | OpenUI examples, all modes | [`04_openui/`](04_openui/) - 4 labs, `@openuidev/lang-core` in Node and browser | ✅ |
| 6 | Harness integration, all modes | [`06_harness/`](06_harness/) - 4 labs, agent loop + terminal/AG-UI surfaces | ✅ |
| 7 | Modes: static, declarative, open-ended **and mixed** for each | `labN_static / declarative / open_ended / mixed` in every part | ✅ 24 labs |
| 8 | Progressive explanation | part READMEs (parts build on each other), [`docs/CONCEPTS.md`](docs/CONCEPTS.md) | ✅ |
| 9 | Full code walkthrough of every codelab | every lab README → "Code walkthrough", numbered steps with real snippets (checked by `tools/check_snippets.py`) | ✅ |
| 10 | Showing execution of the code | every lab: recorded `demo_output.txt` embedded in its README + `screenshot*.png`; [`evidence/`](evidence/) | ✅ |
| 11 | Tests | `test_lab.py` in every lab; `python run_all.py` | ✅ |
| 12 | YouTube video with walkthrough and execution | [https://youtu.be/uwuF1Bnx_bY](https://youtu.be/uwuF1Bnx_bY) - all six parts, every mode, run live | ✅ |
| 13 | Video scripts | [`docs/video-scripts/`](docs/video-scripts/) - combined 10-minute script (PDF) and per-part scripts | ✅ |
| 14 | GitHub repository with all deliverables | this repository | ✅ |
