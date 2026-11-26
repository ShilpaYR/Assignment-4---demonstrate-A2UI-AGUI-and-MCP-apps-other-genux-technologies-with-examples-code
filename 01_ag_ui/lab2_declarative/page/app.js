// AG-UI lab 2 (declarative): the UI is agent STATE; deltas are JSON Patch.
import { createShell } from "/common/shell.js";
import { renderSpec, h } from "/common/ui.js";
import { runAgent, newId } from "/common/agui.js";
import { applyPatch } from "/common/jsonpatch.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 1 · AG-UI", title: "Lab 2 - a catalog layout carried as shared state", mode: "declarative", prompt: PROMPT });

let state = {};                       // the shared state, owned by the agent, mirrored here
const view = h("div");
const chat = h("div");

function paint() {                    // state.ui is a flat element map: render it
  view.replaceChildren(renderSpec(state.ui, { onAction: (a) => shell.log("action", a, "client") }));
}

async function run() {
  shell.clearLog();
  state = {};
  chat.textContent = "";
  shell.canvas.replaceChildren(chat, view);
  await runAgent("/agui", {
    threadId: "thread_declarative",
    messages: [{ id: newId("msg"), role: "user", content: PROMPT }],
  }, (ev) => {
    shell.log(ev.type, ev, ev.type === "RUN_ERROR" ? "error" : "");
    switch (ev.type) {
      case "STEP_STARTED": shell.setStatus(`step: ${ev.stepName} ...`); break;
      case "STATE_SNAPSHOT": state = ev.snapshot; paint(); break;           // replace everything
      case "STATE_DELTA": state = applyPatch(state, ev.delta); paint(); break; // patch, then repaint
      case "TEXT_MESSAGE_START": chat.append(h("div", { class: "chat" }, h("div", { class: "who" }, "assistant"))); break;
      case "TEXT_MESSAGE_CONTENT": chat.lastChild.append(ev.delta); break;
      case "RUN_ERROR": view.replaceChildren(h("div", { class: "g-error" }, ev.message)); break;
      case "RUN_FINISHED": shell.setStatus(`run finished: ${Object.keys(state.ui.elements).length} elements in state.ui`); break;
    }
  });
}

shell.runButton.addEventListener("click", run);
run();
