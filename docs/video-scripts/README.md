# Recording guide - one YouTube video per part

The assignment asks for a video for each part, with a step-by-step code walkthrough **and the code running**. There is one script per part; each is planned for **10-14 minutes**.

| Video | Script | Folder |
|---|---|---|
| 1 | [part1_ag_ui.md](part1_ag_ui.md) | `01_ag_ui/` |
| 2 | [part2_a2ui.md](part2_a2ui.md) | `02_a2ui/` |
| 3 | [part3_json_render.md](part3_json_render.md) | `03_json_render/` |
| 4 | [part4_openui.md](part4_openui.md) | `04_openui/` |
| 5 | [part5_mcp_apps.md](part5_mcp_apps.md) | `05_mcp_apps/` |
| 6 | [part6_harness.md](part6_harness.md) | `06_harness/` |

## Before you record (once)

```bash
python -m venv .venv && source .venv/bin/activate      # Windows: .venv\Scripts\activate
python -m pip install -r requirements.txt
python -m playwright install chromium
npm install && npm run build
python run_all.py                                       # everything should say PASS
```

**Tip:** `python tools/start_all.py` starts all 24 lab servers at once (ports 8011-8064), so every lab page can be open in a browser tab before you record. A single combined 10-minute script is in `GenUX_A4_10min_Video_Script.pdf`.

## Setup for each video

- Screen layout: editor (VS Code) on the left, a terminal at the bottom, the browser on the right. Increase the font size (editor 16 px, terminal 15 px, browser zoom 110-125%).
- Open the part's `README.md` in Markdown preview; every lab README has numbered "Code walkthrough" steps. **Follow them in order** - they are the walkthrough.
- Keep the browser's wire panel (dark, right-hand side of every lab page) visible: it shows the protocol messages, which is what makes each technology different.
- Use YouTube "Unlisted" visibility unless the course says otherwise. Title format: `GenUX Assignment 4 - Part N: <technology> (static, declarative, open-ended, mixed)`.

## The same 4-beat structure for every lab (about 2.5-3 minutes each)

1. **Say the mode in one sentence** (read the lab README's first paragraph).
2. **Run it**: `python server.py` (or `run_host.py` / `agent.py --web`), open the URL, click the things the demo clicks. Point at the wire panel.
3. **Walk the code**: the README's Step 1 → Step N, opening each named file at the snippet.
4. **Prove it**: run `python demo.py` (recorded output + official-library checks) and `python -m pytest test_lab.py`.

Close each video with the part README's comparison table and one sentence on what the next part changes.

## Recorded video

[https://youtu.be/uwuF1Bnx_bY](https://youtu.be/uwuF1Bnx_bY)
