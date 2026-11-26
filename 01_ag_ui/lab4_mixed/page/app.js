// AG-UI lab 4 (mixed): catalog UI + one sandboxed generated region,
// with three round trips back to the agent (action, client tool, sandbox event).
import { createShell } from "/common/shell.js";
import { renderSpec, h } from "/common/ui.js";
import { runAgent, newId } from "/common/agui.js";
import { applyPatch } from "/common/jsonpatch.js";

const PROMPT = "Show this week's dashboard, and add an interactive what-if price calculator that the standard components cannot express.";
const shell = createShell({ part: "Part 1 · AG-UI", title: "Lab 4 - catalog + sandboxed region + human in the loop", mode: "mixed", prompt: PROMPT });

// A tool the PAGE implements. The agent may call it; the page decides what it does.
const TOOLS = [{
  name: "confirm_restock",
  description: "Ask the user to approve a coffee-bean order. Returns {approved: boolean}.",
  parameters: { type: "object", properties: { kg: { type: "number" }, cost_usd: { type: "number" } }, required: ["kg"] },
}];

let state = {};
let messages = [];
const chat = h("div");
const view = h("div");
const ctx = {
  allowedEvents: ["apply_price"],
  onAction: (action, params) => send({ action, params }),                         // 1. catalog Button
  onGeneratedEvent: (name, payload) => {                                         // 3. sandbox event
    shell.log(`iframe -> page: ${name}`, payload, "client");
    if (name !== "rejected") send({ action: name, params: payload });
  },
};

function paintAll() { view.replaceChildren(renderSpec(state.ui, ctx)); }

// Re-render only the elements a delta touched, so the sandboxed iframe is not reloaded.
function paintChanged(delta) {
  const ids = new Set(delta.map((op) => op.path.split("/")[3]).filter(Boolean));
  for (const id of ids) {
    const old = view.querySelector(`[data-id="${id}"]`);
    if (old) old.replaceWith(renderSpec({ root: id, elements: state.ui.elements }, ctx));
  }
}

function confirmDialog(callId, args) {                                           // 2. client tool
  const box = h("div", { class: "dialog" },
    h("strong", {}, `Approve ordering ${args.kg} kg of beans for $${args.cost_usd.toFixed(2)}?`), h("br"),
    h("button", { id: "approve", onClick: () => answer(true) }, "Approve"), " ",
    h("button", { class: "secondary", onClick: () => answer(false) }, "Cancel"));
  function answer(approved) {
    box.remove();
    messages.push({ id: newId("msg"), role: "tool", toolCallId: callId, content: JSON.stringify({ approved }) });
    send({});
  }
  chat.append(box);
}

function handle(ev, pending) {
  shell.log(ev.type, ev, ev.type === "RUN_ERROR" ? "error" : "");
  switch (ev.type) {
    case "STATE_SNAPSHOT": state = ev.snapshot; paintAll(); break;
    case "STATE_DELTA": state = applyPatch(state, ev.delta); paintChanged(ev.delta); break;
    case "TEXT_MESSAGE_START": chat.append(h("div", { class: "chat" }, h("div", { class: "who" }, "assistant"))); break;
    case "TEXT_MESSAGE_CONTENT": chat.lastChild.append(ev.delta); break;
    case "TEXT_MESSAGE_END":                    // keep the conversation history complete
      messages.push({ id: ev.messageId, role: "assistant", content: chat.lastChild.lastChild.textContent });
      break;
    case "TOOL_CALL_START": pending[ev.toolCallId] = { name: ev.toolCallName, args: "" }; break;
    case "TOOL_CALL_ARGS": pending[ev.toolCallId].args += ev.delta; break;
    case "TOOL_CALL_END": {
      const call = pending[ev.toolCallId];
      // remember the call in the conversation, then execute it here in the page
      messages.push({ id: newId("msg"), role: "assistant", toolCalls: [{ id: ev.toolCallId, type: "function", function: { name: call.name, arguments: call.args } }] });
      if (call.name === "confirm_restock") confirmDialog(ev.toolCallId, JSON.parse(call.args));
      break;
    }
    case "RUN_ERROR": chat.append(h("div", { class: "g-error" }, ev.message)); break;
    case "RUN_FINISHED": shell.setStatus(`run finished · beans on hand: ${state.inventory?.beans_kg} kg`); break;
  }
}

async function send(forwardedProps) {
  const pending = {};
  await runAgent("/agui", { threadId: "thread_mixed", messages, state, tools: TOOLS, forwardedProps }, (ev) => handle(ev, pending));
}

async function start() {
  shell.clearLog();
  state = {};
  messages = [{ id: newId("msg"), role: "user", content: PROMPT }];
  shell.canvas.replaceChildren(chat, view);
  chat.textContent = "";
  await send({});
}

shell.runButton.addEventListener("click", start);
start();
