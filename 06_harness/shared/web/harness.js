// The harness's web surface: an AG-UI client that shows the agent loop and renders its UI tools.
import { createShell } from "/common/shell.js";
import { components, renderSpec, h } from "/common/ui.js";
import { runAgent, newId } from "/common/agui.js";
import { applyPatch } from "/common/jsonpatch.js";
import { mountSandboxed } from "/common/sandbox.js";

const cfg = await (await fetch("/config")).json();
const shell = createShell({ part: cfg.part, title: cfg.title, mode: cfg.mode, prompt: cfg.prompt });
const STATIC = { show_metric: components.Metric, show_chart: components.BarChart, show_table: components.Table };

const transcript = h("div");
const view = h("div");
let state = {};
const ctx = {
  allowedEvents: ["apply_price"],
  onAction: (action, params) => send({ action, params }),                      // UI action -> next harness turn
  onGeneratedEvent: (name, payload) => { shell.log(`iframe -> page: ${name}`, payload, "client"); if (name !== "rejected") send({ action: name, params: payload }); },
};

function paintChanged(delta) {                    // keep sandboxed regions alive: patch only touched elements
  for (const id of new Set(delta.map((op) => op.path.split("/")[3]).filter(Boolean))) {
    view.querySelector(`[data-id="${id}"]`)?.replaceWith(renderSpec({ root: id, elements: state.ui.elements }, ctx));
  }
}

function handle(ev, calls, staticRow) {
  if (ev.type !== "TOOL_CALL_ARGS") shell.log(ev.type, ev, ev.type === "RUN_ERROR" ? "error" : "");
  switch (ev.type) {
    case "TEXT_MESSAGE_START": transcript.append(h("div", { class: "chat" }, h("div", { class: "who" }, "assistant"))); break;
    case "TEXT_MESSAGE_CONTENT": transcript.lastChild.append(ev.delta); break;
    case "TOOL_CALL_START": calls[ev.toolCallId] = { name: ev.toolCallName, args: "" }; break;
    case "TOOL_CALL_ARGS": calls[ev.toolCallId].args += ev.delta; break;
    case "TOOL_CALL_END": {
      const c = calls[ev.toolCallId];
      const short = c.args.length > 90 ? c.args.slice(0, 90) + " ..." : c.args;
      c.chip = h("div", { class: "g-text muted", "data-tool": c.name }, `🔧 ${c.name}(${short})`);
      transcript.append(c.chip);
      if (STATIC[c.name]) staticRow(c.name).append(STATIC[c.name](JSON.parse(c.args)));   // static UI tools
      break;
    }
    case "TOOL_CALL_RESULT": {
      const c = calls[ev.toolCallId];
      if (c && ev.content.startsWith('{"error"')) c.chip.append(h("span", { style: "color:var(--bad)" }, `  -> rejected: ${ev.content.slice(10, 170)}`));
      break;
    }
    case "STATE_SNAPSHOT": state = ev.snapshot; view.replaceChildren(renderSpec(state.ui, ctx)); break;   // render_ui
    case "STATE_DELTA": state = applyPatch(state, ev.delta.map((op) => ({ ...op, path: "/ui" + op.path }))); paintChanged(ev.delta.map((op) => ({ ...op, path: "/ui" + op.path }))); break;
    case "ACTIVITY_SNAPSHOT": {                                                                         // render_html
      const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, ev.content.title), h("span", {}, `sandboxed · ${ev.content.tokens} tokens`)));
      view.replaceChildren(box);
      mountSandboxed(box, ev.content.html, ctx.allowedEvents && { allowed: ctx.allowedEvents, onEvent: ctx.onGeneratedEvent });
      break;
    }
    case "RUN_FINISHED": shell.setStatus("run finished · tool calls, text and UI all came from one agent loop"); break;
  }
}

async function send(forwardedProps = {}, text = null) {
  const calls = {};
  let row = null;
  const staticRow = (name) => {
    if (name === "show_metric") { if (!row) { row = h("div", { class: "g-row" }); view.append(row); } return row; }
    return view;
  };
  const messages = text ? [{ id: newId("msg"), role: "user", content: text }] : [];
  await runAgent("/agui", { threadId: "harness", messages, forwardedProps }, (ev) => handle(ev, calls, staticRow));
}

shell.runButton.addEventListener("click", () => { shell.clearLog(); transcript.textContent = ""; view.textContent = ""; send({}, cfg.prompt); });
shell.canvas.append(transcript, view);
send({}, cfg.prompt);
