// The browser half of our MCP Apps host: mount the view, run the JSON-RPC bridge.
import { createShell } from "/common/shell.js";
import { h } from "/common/ui.js";
import { postJSON } from "/common/sse.js";

const cfg = await (await fetch("/host/config")).json();
const shell = createShell({ part: cfg.part, title: cfg.title, mode: cfg.mode, prompt: cfg.prompt, runLabel: "Ask the agent" });
window.__bridgeLog = [];                                   // every bridge message, for the conformance test

// CSP for the view, built from the resource's _meta.ui.csp (empty lists = no network at all).
function viewCsp(meta) {
  const csp = meta?.ui?.csp || {};
  const res = (csp.resourceDomains || []).join(" ");
  return [
    "default-src 'none'", `script-src 'unsafe-inline' ${res}`, `style-src 'unsafe-inline' ${res}`, `img-src data: ${res}`,
    `connect-src ${(csp.connectDomains || []).join(" ") || "'none'"}`, "frame-src 'self' about: data:", "base-uri 'none'",
  ].join("; ");
}

function mountView(resource, tool, args, result) {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${viewCsp(resource._meta)}">`;
  const html = resource.text.replace(/<head[^>]*>/i, (m) => m + meta);
  const frame = h("iframe", { class: "genux-sandbox", sandbox: "allow-scripts", style: "height:420px" });
  frame.srcdoc = html;
  const box = h("div", { class: "g-card" }, h("div", { class: "sub" }, `MCP App view · ${resource.uri} · sandbox="allow-scripts"`), frame);
  shell.canvas.append(box);

  const send = (msg) => { window.__bridgeLog.push({ dir: "host->view", msg }); shell.log(`host -> view ${msg.method || "result"}`, msg); frame.contentWindow.postMessage(msg, "*"); };
  const reply = (id, result) => send({ jsonrpc: "2.0", id, result });
  const fail = (id, code, message) => send({ jsonrpc: "2.0", id, error: { code, message } });

  window.addEventListener("message", async (e) => {
    if (e.source !== frame.contentWindow) return;          // only our view
    const m = e.data;
    if (!m || m.jsonrpc !== "2.0") return;
    window.__bridgeLog.push({ dir: "view->host", msg: m });
    if (m.method !== "ui/notifications/size-changed") shell.log(`view -> host ${m.method}`, m, "client");
    switch (m.method) {
      case "ui/initialize":
        return reply(m.id, {
          protocolVersion: "2026-01-26",
          hostInfo: { name: "genux-course-host", version: "1.0.0" },
          hostCapabilities: { serverTools: {}, updateModelContext: { text: {} }, message: { text: {} } },
          hostContext: { theme: "light", displayMode: "inline", toolInfo: { tool }, locale: "en-US" },
        });
      case "ui/notifications/initialized":                // now the view is listening: hand it the call
        send({ jsonrpc: "2.0", method: "ui/notifications/tool-input", params: { arguments: args } });
        return send({ jsonrpc: "2.0", method: "ui/notifications/tool-result", params: result });
      case "ui/notifications/size-changed":
        frame.style.height = `${Math.min(1400, Math.max(120, m.params.height))}px`;
        return;
      case "tools/call": {                                 // the view calls a server tool THROUGH the host
        const out = await postJSON("/host/call", { name: m.params.name, arguments: m.params.arguments, caller: "app" });
        return out.error ? fail(m.id, -32602, out.error) : reply(m.id, out.result);
      }
      case "ui/message":
        await postJSON("/host/message", m.params);
        shell.canvas.insertBefore(h("div", { class: "chat" }, h("div", { class: "who" }, "user message sent by the app"), m.params.content.map((c) => c.text).join(" ")), box);
        return reply(m.id, {});
      case "ui/update-model-context":
        await postJSON("/host/context", m.params);
        shell.setStatus(`model context updated by the app: "${m.params.content.map((c) => c.text).join(" ")}"`);
        return reply(m.id, {});
      default:
        if ("id" in m) fail(m.id, -32601, `method not supported by this host: ${m.method}`);
    }
  });
}

async function run() {
  shell.clearLog();
  shell.canvas.textContent = "";
  const tools = await (await fetch("/host/tools")).json();
  shell.log("tools/list", tools.map((t) => ({ name: t.name, ui: t._meta?.ui })));
  // A real host lets the MODEL pick the tool; here the lab fixes it so the run is reproducible.
  const out = await postJSON("/host/call", { name: cfg.tool, arguments: cfg.arguments, caller: "model" });
  shell.log(`tools/call ${cfg.tool}`, out.result);
  shell.canvas.append(h("div", { class: "chat" }, h("div", { class: "who" }, "tool result text (what the model reads)"), out.result.content.map((c) => c.text).join("\n")));
  if (out.resource) {
    shell.log("resources/read", { uri: out.resource.uri, mimeType: out.resource.mimeType, _meta: out.resource._meta, bytes: out.resource.text.length });
    mountView(out.resource, out.tool, cfg.arguments, out.result);
    shell.setStatus("view mounted from the ui:// resource; the bridge is live");
  }
}

shell.runButton.addEventListener("click", run);
run();
