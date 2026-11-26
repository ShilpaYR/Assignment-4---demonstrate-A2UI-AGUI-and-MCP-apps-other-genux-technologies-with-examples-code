"""A minimal MCP Apps HOST: an MCP client plus a web page that mounts UI resources.

Real hosts (Claude, ChatGPT, VS Code, Goose, ...) do three things for an MCP App:
1. connect to the MCP server and call its tools (here: the official Python SDK's
   ``mcp.Client`` over stdio, kept open in a background thread);
2. when a called tool has ``_meta.ui.resourceUri``, read that resource and render
   it in a sandboxed iframe;
3. run the JSON-RPC bridge between the iframe and the server
   (``host_page/host.js``): initialize, forward the tool input/result,
   proxy the view's ``tools/call`` - enforcing ``_meta.ui.visibility`` -,
   and receive ``ui/message`` and ``ui/update-model-context``.

The browser cannot speak stdio, so the page calls this backend's /host/* routes.

    from host import build_host
    build_host(lab_dir, title=..., mode=..., prompt=..., tool=..., arguments={...}).serve(port)
"""

from __future__ import annotations

import asyncio
import sys
import threading
from pathlib import Path

from mcp import Client, StdioServerParameters

SHARED = Path(__file__).resolve().parent
sys.path.insert(0, str(SHARED.parents[1]))

from common.web import App  # noqa: E402
from mcpapps import dump  # noqa: E402


class McpConnection:
    """One long-lived MCP client session (stdio) driven from synchronous code."""

    def __init__(self, server_script: Path):
        self.params = StdioServerParameters(command=sys.executable, args=[str(server_script), "--stdio"])
        self.loop = asyncio.new_event_loop()
        self.ready, self.stop = threading.Event(), None
        threading.Thread(target=self.loop.run_forever, daemon=True).start()
        asyncio.run_coroutine_threadsafe(self._session(), self.loop)
        if not self.ready.wait(30):
            raise RuntimeError(f"MCP server {server_script} did not start")

    async def _session(self):
        self.stop = asyncio.Event()
        async with Client(self.params) as client:
            self.client = client
            self.ready.set()
            await self.stop.wait()

    def run(self, coro_fn, *args):
        return asyncio.run_coroutine_threadsafe(coro_fn(*args), self.loop).result(60)

    def tools(self) -> list[dict]:
        return [dump(t) for t in self.run(self.client.list_tools).tools]

    def call(self, name: str, arguments: dict) -> dict:
        return dump(self.run(self.client.call_tool, name, arguments))

    def resource(self, uri: str) -> dict:
        return dump(self.run(self.client.read_resource, uri))["contents"][0]


def visibility(tool: dict) -> list[str]:
    return ((tool.get("_meta") or {}).get("ui") or {}).get("visibility") or ["model", "app"]


def build_host(lab_dir: Path, *, title: str, mode: str, prompt: str, tool: str, arguments: dict) -> App:
    lab_dir = Path(lab_dir)
    conn = McpConnection(lab_dir / "server.py")
    app = App(SHARED / "host_page", title=f"MCP host for {lab_dir.name}")
    state = {"context": [], "messages": []}

    def find(name):
        return next((t for t in conn.tools() if t["name"] == name), None)

    @app.get("/host/config")
    def config(req):
        return {"part": "Part 5 · MCP Apps", "title": title, "mode": mode, "prompt": prompt, "tool": tool, "arguments": arguments}

    @app.get("/host/tools")
    def tools(req):
        return conn.tools()

    @app.post("/host/call")
    def call(req):
        body = req.json()
        caller = body.get("caller", "model")            # "model" (the agent) or "app" (the view)
        t = find(body["name"])
        if t is None or caller not in visibility(t):     # the host enforces _meta.ui.visibility
            return {"error": f"tool {body['name']!r} is not visible to the {caller}"}
        out = {"tool": t, "result": conn.call(body["name"], body.get("arguments") or {})}
        uri = ((t.get("_meta") or {}).get("ui") or {}).get("resourceUri")
        if caller == "model" and uri:                    # a UI-capable host fetches the view
            out["resource"] = conn.resource(uri)
        return out

    @app.post("/host/message")
    def message(req):                                    # ui/message: the view speaks to the chat
        state["messages"].append(req.json())
        return {}

    @app.post("/host/context")
    def context(req):                                    # ui/update-model-context: what the model will see next turn
        state["context"] = req.json().get("content", [])
        return {}

    @app.get("/host/state")
    def host_state(req):
        return state

    return app
