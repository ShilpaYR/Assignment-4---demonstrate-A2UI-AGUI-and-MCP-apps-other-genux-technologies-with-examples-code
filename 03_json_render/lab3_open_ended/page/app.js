// json-render lab 3 (open-ended): one HtmlBlock; its on-map decides which events may leave the sandbox.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { JsonRenderView } from "/jr/jr-render.js";

const PROMPT = "Build an interactive break-even calculator for the coffee cart: sliders for price per cup, cost per cup and fixed weekly costs.";
const shell = createShell({ part: "Part 3 · json-render", title: "Lab 3 - a one-component catalog: HtmlBlock", mode: "open-ended", prompt: PROMPT });

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
    shell.log(op.path === "" ? "spec" : `patch ${op.path}`, op);
    view.applyPatches([op]);
  });
  shell.setStatus("one HtmlBlock: free-form inside, json-render (state, on-bindings, actions) outside");
}

shell.runButton.addEventListener("click", run);
run();
