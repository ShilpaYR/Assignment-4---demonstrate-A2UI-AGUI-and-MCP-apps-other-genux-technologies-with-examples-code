# Video 5 - MCP Apps: UI inside a host you do not control (≈13 min)

**Goal:** show the three additions to an MCP server, the host's job, the JSON-RPC bridge, visibility, and that our bridge traffic matches the official ext-apps schemas.

| Time | On screen | Do | Say |
|---|---|---|---|
| 0:00 | `05_mcp_apps/README.md` | Sequence diagram | "MCP Apps: a ui:// resource, a tool that points at it, and a result with text and structured data. The host mounts the view in a sandboxed iframe and runs a JSON-RPC bridge over postMessage." |
| 1:00 | `shared/host.py`, `shared/host_page/host.js`, `shared/view-bridge.js` | Scroll | "Our host: the official MCP Python SDK as a stdio client, plus a page that mounts views. The view bridge uses the same method names as the official App class." |
| 2:00 | lab1_static: `python run_host.py` (8051) | Click "Last 3 days", "Reorder", "Ask about Friday" | "Static: a pre-built view." Wire: ui/initialize → initialized → tool-input → tool-result → tools/call → ui/message. |
| 3:00 | `server.py`, `shared/mcpapps.py`, `host.js` | README steps 1-6 | "`_meta.ui.resourceUri`, `visibility`, `text/html;profile=mcp-app`, the CSP declaration. The host enforces visibility: the model can't call restock_beans." |
| 4:30 | Terminal | `python demo.py` | "@modelcontextprotocol/ext-apps schemas: 8 messages checked, errors=[]". |
| 5:00 | lab2_declarative (8052) | Reorder | "Declarative: the view is a generic catalog renderer; the server's model designs the layout; the key never leaves the server." |
| 5:45 | `server.py`, `view.html`, `shared/view-kit-entry.js` | Steps 1-4 | "isError results let the model retry; ui_action is app-only and returns JSON Patch." |
| 7:00 | lab3_open_ended (8053) | Use the calculator → "Use this price" | "Open-ended: generated HTML two sandboxes deep - host, view, widget. The view decides what reaches the host: ui/update-model-context." |
| 7:45 | `server.py`, `view.html` | Steps 1-4 | "update-model-context doesn't start a turn; it changes what the model knows next time." |
| 9:00 | lab4_mixed (8054) + terminal `python ../shared/text_host.py server.py coffee_dashboard_hybrid '{"request":"dashboard"}'` | Use calculator, Reorder; run the text host | "Mixed: catalog plus generated region, two app-only tools. And ship both: a host without UI still gets a full text answer." |
| 10:00 | `server.py`, `view.html`, `shared/text_host.py` | Steps 1-5 | "Host refuses the model calling apply_price; the server refuses price 40. Two independent checks." |
| 11:30 | Terminal | `python demo.py`, pytest | — |
| 12:00 | Part README "Use the servers in a real host" | Show the Claude Desktop config | "Each server.py works in a real MCP host over stdio. (Optional: if you have Claude Desktop, add the config and show the view there.)" |
| 12:40 | — | — | "Next: generative UI inside a coding-agent harness." |
