// The View side of the MCP Apps bridge (SEP-1865), in ~60 lines.
//
// A view is an HTML document that a HOST (Claude, ChatGPT, VS Code, Goose, our
// host page ...) renders in a sandboxed iframe. It talks to the host with
// JSON-RPC 2.0 over postMessage:
//   view -> host  requests:      ui/initialize, tools/call, ui/message, ui/update-model-context
//   view -> host  notifications: ui/notifications/initialized, ui/notifications/size-changed
//   host -> view  notifications: ui/notifications/tool-input, ui/notifications/tool-result
// The official SDK (@modelcontextprotocol/ext-apps, class App) offers the same
// methods with the same names; this hand-written copy shows the wire format.
class McpAppBridge {
  constructor(appInfo) {
    this.appInfo = appInfo;
    this.nextId = 1;
    this.pending = new Map();
    this.ontoolinput = null;
    this.ontoolresult = null;
    window.addEventListener("message", (e) => {
      if (e.source !== window.parent) return;               // only the host may talk to us
      const m = e.data;
      if (!m || m.jsonrpc !== "2.0") return;
      if ("id" in m && this.pending.has(m.id)) {             // a response to one of our requests
        const { resolve, reject } = this.pending.get(m.id);
        this.pending.delete(m.id);
        return m.error ? reject(new Error(m.error.message)) : resolve(m.result);
      }
      if (m.method === "ui/notifications/tool-input") this.ontoolinput?.(m.params);
      if (m.method === "ui/notifications/tool-result") this.ontoolresult?.(m.params);
    });
  }
  request(method, params) {
    const id = this.nextId++;
    window.parent.postMessage({ jsonrpc: "2.0", id, method, params }, "*");
    return new Promise((resolve, reject) => this.pending.set(id, { resolve, reject }));
  }
  notify(method, params) { window.parent.postMessage({ jsonrpc: "2.0", method, params }, "*"); }

  async connect() {
    const result = await this.request("ui/initialize", { appInfo: this.appInfo, appCapabilities: {}, protocolVersion: "2026-01-26" });
    this.hostContext = result.hostContext;
    this.notify("ui/notifications/initialized", {});
    new ResizeObserver(() => this.notify("ui/notifications/size-changed", {
      width: document.documentElement.scrollWidth, height: Math.ceil(document.body.getBoundingClientRect().bottom) + 16,
    })).observe(document.body);
    return result;
  }
  callServerTool(name, args) { return this.request("tools/call", { name, arguments: args }); }
  sendMessage(text) { return this.request("ui/message", { role: "user", content: [{ type: "text", text }] }); }
  updateModelContext(text) { return this.request("ui/update-model-context", { content: [{ type: "text", text }] }); }
}
