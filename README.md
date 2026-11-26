# GenUX Assignment 4 - Generative UI: AG-UI, A2UI, json-render, OpenUI, MCP Apps and harness integration

Runnable codelabs that demonstrate six generative-UI technologies, each in **all four generation modes** (**static, declarative, open-ended and mixed**). That makes **24 labs**. Every lab has a step-by-step code walkthrough, a recorded run (terminal output and browser screenshots) and offline tests. Where an official library exists, the lab also includes a conformance check that uses it.

One scenario runs through every lab, so the technologies can be compared directly: a weekly sales dashboard for a **Campus Coffee Cart**, plus an interactive *break-even calculator* that no standard component can express.

## Video

**▶ Walkthrough and live demo: [https://youtu.be/uwuF1Bnx_bY](https://youtu.be/uwuF1Bnx_bY)**

The video covers all six parts and all four modes of each: it runs every lab in the browser, shows the protocol messages in each page's wire panel, walks through the code, and finishes with the full test run.

[![GenUX Assignment 4 video](https://img.youtube.com/vi/uwuF1Bnx_bY/hqdefault.jpg)](https://youtu.be/uwuF1Bnx_bY)

## The matrix: 6 technologies × 4 modes

| | Static | Declarative | Open-ended | Mixed (hybrid) |
|---|---|---|---|---|
| **[1 · AG-UI](01_ag_ui/)** - event transport | [tool calls → pre-built components](01_ag_ui/lab1_static/) | [catalog layout as shared state (JSON Patch)](01_ag_ui/lab2_declarative/) | [streamed HTML → sandbox](01_ag_ui/lab3_open_ended/) | [catalog + GeneratedView + client tool / human in the loop](01_ag_ui/lab4_mixed/) |
| **[2 · A2UI v1.0](02_a2ui/)** - Google's declarative format | [developer surface, agent data model](02_a2ui/lab1_static/) | [model-written surface + correction loop](02_a2ui/lab2_declarative/) | [custom catalog: HtmlFrame](02_a2ui/lab3_open_ended/) | [basic + custom catalog on one surface](02_a2ui/lab4_mixed/) |
| **[3 · json-render](03_json_render/)** - Vercel's catalog renderer | [template spec + agent state](03_json_render/lab1_static/) | [SpecStream validated per line](03_json_render/lab2_declarative/) | [HtmlBlock-only catalog](03_json_render/lab3_open_ended/) | [hybrid catalog, actions, terminal renderer](03_json_render/lab4_mixed/) |
| **[4 · OpenUI Lang](04_openui/)** - compact UI language | [library of pre-built components](04_openui/lab1_static/) | [primitives, forward refs, token benchmark](04_openui/lab2_declarative/) | [HtmlArtifact only](04_openui/lab3_open_ended/) | [primitives + HtmlArtifact, statement edits](04_openui/lab4_mixed/) |
| **[5 · MCP Apps](05_mcp_apps/)** - UI inside a third-party host | [pre-built view for a tool result](05_mcp_apps/lab1_static/) | [generic catalog-renderer view](05_mcp_apps/lab2_declarative/) | [generated HTML, nested sandbox](05_mcp_apps/lab3_open_ended/) | [catalog + generated region, app-only tools, text host](05_mcp_apps/lab4_mixed/) |
| **[6 · Harness](06_harness/)** - UI tools in an agent loop | [`show_*` tools, terminal + web surfaces](06_harness/lab1_static/) | [`render_ui` + self-correction](06_harness/lab2_declarative/) | [`render_html` → artifact + sandbox](06_harness/lab3_open_ended/) | [clicks become turns; workspace + UI updates](06_harness/lab4_mixed/) |

The modes are explained, and compared across all six technologies, in **[docs/CONCEPTS.md](docs/CONCEPTS.md)**.

## Quick start

```bash
# Python 3.10+ and Node 20+ (tested: Python 3.13, Node 22)
python -m venv .venv && source .venv/bin/activate          # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium                       # for demo screenshots
npm install && npm run build                                # official JS libraries + generated prompts/bundles

python run_all.py                                           # tests for all 24 labs + README snippet check
python run_all.py --demos                                   # also re-record every demo and screenshot
```

Run any single lab:

```bash
cd 01_ag_ui/lab1_static && python server.py                 # open the printed URL
cd 05_mcp_apps/lab1_static && python run_host.py            # MCP Apps labs run inside our host
cd 06_harness/lab1_static && python agent.py [--web]        # harness labs: terminal or web surface
python demo.py                                              # in any lab: the recorded run
python -m pytest test_lab.py                                # in any lab: offline tests
```

**No API key needed.** By default every model call is replayed from the lab's `fixtures/` (see `common/llm.py`). To use a real model with the same prompts, validation and renderers, set `GENUX_LIVE=1` and `API_KEY` (or `OPENAI_API_KEY`). `BASE_URL` and `MODEL` are optional; the default model is `gpt-4.1-mini`.

## Evidence that it runs

- [`evidence/TEST_REPORT.md`](evidence/TEST_REPORT.md): per-lab test results, produced by `python run_all.py`
- [`evidence/DEMO_LOG.md`](evidence/DEMO_LOG.md): per-lab demo results and screenshots, produced by `tools/record_demos.py`
- Each lab README embeds its recorded terminal output and its `screenshot*.png` files
- Conformance with the official libraries:
  - every A2UI stream is accepted by Google's `@a2ui/web_core` processor
  - every json-render spec passes `@json-render/core`
  - every OpenUI program parses with `@openuidev/lang-core`
  - every recorded MCP Apps bridge message validates against the `@modelcontextprotocol/ext-apps` schemas
- [`tools/check_snippets.py`](tools/check_snippets.py) verifies that every code snippet in every walkthrough exists verbatim in the file it names

## Repository layout

```text
common/            shared by all labs: scenario data, LLM client (scripted/live), tiny HTTP+SSE server,
                   catalog validator, JSON Patch, HTML sandbox policy, token counter, demo helpers
  web/             shared browser modules: page shell + wire panel, components, sandbox, SSE, AG-UI client
01_ag_ui/ … 06_harness/
  README.md        the part: what the technology is, the four labs, a comparison
  shared/          the part's own helpers (schemas, catalogs, renderers, host, harness)
  labN_<mode>/     README.md (walkthrough) · server.py / agent.py · page/ or view.html · fixtures/
                   demo.py · demo_output.txt · screenshot*.png · test_lab.py
docs/              CONCEPTS.md, video-scripts/ (one per part)
tools/             make_fixtures.py, record_demos.py, check_snippets.py
evidence/          TEST_REPORT.md, DEMO_LOG.md
```

## Versions and sources

- Python: `ag-ui-protocol` 1.0.0, `mcp` 2.3.0 (MCPServer / Client), `jsonschema`, `rich`, `playwright`
- npm: `@a2ui/web_core` 0.16.1, `@json-render/core` 0.23.2, `@openuidev/lang-core` 1.2.0, `@modelcontextprotocol/ext-apps` 2.0.4, `gpt-tokenizer`, `esbuild`
- A2UI schemas: the official v1.0 JSON Schemas (Apache-2.0), see [`02_a2ui/shared/schema/NOTICE.md`](02_a2ui/shared/schema/NOTICE.md)
- Course reference: [dlmastery/simple-coding-harness/genui](https://github.com/dlmastery/simple-coding-harness/tree/main/genui). This repository is an independent implementation built around one shared scenario, so that the 6 × 4 modes can be compared side by side.

Built with AI coding assistance. Every lab was run, tested and recorded as shown above and in the video.

## License

MIT (see [LICENSE](LICENSE)). Third-party schema files keep their own licenses.
