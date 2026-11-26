// AG-UI lab 1 (static): tool calls select pre-built components.
import { createShell } from "/common/shell.js";
import { components, h } from "/common/ui.js";
import { runAgent, newId } from "/common/agui.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 1 · AG-UI", title: "Lab 1 - tool calls pick pre-built components", mode: "static", prompt: PROMPT });

// The static part: one hand-written renderer per tool. The agent cannot add new ones.
const RENDERERS = {
  show_metric: (a) => components.Metric(a),
  show_chart: (a) => components.BarChart(a),
  show_table: (a) => components.Table(a),
};

async function run() {
  shell.canvas.textContent = "";
  shell.clearLog();
  const row = h("div", { class: "g-row" });           // metrics go side by side
  const pending = {};                                  // toolCallId -> { name, args, slot }
  let chat = null;
  shell.canvas.append(row);

  await runAgent("/agui", {
    threadId: "thread_static",
    messages: [{ id: newId("msg"), role: "user", content: PROMPT }],
  }, (ev) => {
    shell.log(ev.type, ev);
    switch (ev.type) {
      case "RUN_STARTED": shell.setStatus("run started ..."); break;
      case "TEXT_MESSAGE_START": chat = h("div", { class: "chat" }, h("div", { class: "who" }, "assistant"));
        row.before(chat); break;
      case "TEXT_MESSAGE_CONTENT": chat.append(ev.delta); break;
      case "TOOL_CALL_START": {                        // reserve a slot as soon as the call starts
        const slot = h("div", { class: "g-skeleton" }, `rendering ${ev.toolCallName} ...`);
        (ev.toolCallName === "show_metric" ? row : shell.canvas).append(slot);
        pending[ev.toolCallId] = { name: ev.toolCallName, args: "", slot };
        break;
      }
      case "TOOL_CALL_ARGS": pending[ev.toolCallId].args += ev.delta; break;
      case "TOOL_CALL_END": {                          // arguments complete: draw the component
        const call = pending[ev.toolCallId];
        const render = RENDERERS[call.name];
        call.slot.replaceWith(render ? render(JSON.parse(call.args)) : h("div", { class: "g-error" }, `no renderer for ${call.name}`));
        break;
      }
      case "RUN_FINISHED": shell.setStatus("run finished: every component above was chosen by a tool call"); break;
    }
  });
}

shell.runButton.addEventListener("click", run);
run();
