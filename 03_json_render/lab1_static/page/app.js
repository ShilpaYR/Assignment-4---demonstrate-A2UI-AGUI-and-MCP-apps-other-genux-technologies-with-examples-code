// json-render lab 1 (static): developer template + agent state, as SpecStream patches.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { JsonRenderView } from "/jr/jr-render.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 3 · json-render", title: "Lab 1 - template spec bound to agent state", mode: "static", prompt: PROMPT });

async function run() {
  shell.clearLog();
  const view = new JsonRenderView(shell.canvas, {
    log: shell.log,
    onAction: async (action, params) => {             // custom actions go to the server; it answers with patches
      shell.log(`action -> ${action}`, params, "client");
      const ops = await postJSON("/jr/action", { action, params, state: view.spec.state });
      shell.log("patches <-", ops);
      view.applyPatches(ops);
    },
  });
  await postSSE("/jr/stream", { prompt: PROMPT }, (op) => {
    shell.log(op.path === "" ? "spec (developer template)" : `patch ${op.path}`, op);
    view.applyPatches([op]);
  });
  shell.setStatus("elements: developer template · values: agent state via $state · toggle: built-in setState");
}

shell.runButton.addEventListener("click", run);
run();
