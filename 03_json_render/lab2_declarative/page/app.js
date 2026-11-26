// json-render lab 2 (declarative): apply SpecStream patches as they arrive; measure first paint.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { JsonRenderView } from "/jr/jr-render.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 3 · json-render", title: "Lab 2 - SpecStream: validated patch by patch", mode: "declarative", prompt: PROMPT });

async function run() {
  shell.clearLog();
  const view = new JsonRenderView(shell.canvas, {
    log: shell.log,
    onAction: async (action, params) => {
      shell.log(`action -> ${action}`, params, "client");
      view.applyPatches(await postJSON("/jr/action", { action, params }));
    },
  });
  const t0 = performance.now();
  let firstPaint = null;
  await postSSE("/jr/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {                         // server reports: a rejected line, or the summary
      if (msg.rejected && !msg.done) shell.log(`rejected ${msg.rejected}`, msg.errors.join("; "), "error");
      if (msg.done) {
        const total = Math.round(performance.now() - t0);
        shell.log("summary", msg, msg.issues.length ? "error" : "ok");
        shell.setStatus(`first element painted after ${firstPaint} ms · complete after ${total} ms · ${msg.elements} elements · ${msg.rejected.length} line(s) rejected`);
      }
      return;
    }
    shell.log(`${msg.op} ${msg.path}`, msg);
    view.applyPatches([msg]);                         // render after EVERY patch
    if (firstPaint === null && msg.path.startsWith("/elements/")) firstPaint = Math.round(performance.now() - t0);
  });
}

shell.runButton.addEventListener("click", run);
run();
