// json-render lab 4 (mixed): hybrid catalog, local setState, server actions, and a terminal twin.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { h } from "/common/ui.js";
import { JsonRenderView } from "/jr/jr-render.js";

const PROMPT = "Show this week's dashboard, and add an interactive what-if price calculator that the standard components cannot express.";
const shell = createShell({ part: "Part 3 · json-render", title: "Lab 4 - hybrid catalog, one spec, two renderers", mode: "mixed", prompt: PROMPT });

async function run() {
  shell.clearLog();
  const web = h("div");
  const term = h("pre", { class: "chat", id: "terminal", style: "font:11px/1.25 var(--mono);overflow:auto" });
  shell.canvas.replaceChildren(web, h("div", { class: "status" }, "Second target - the same spec rendered for a terminal (GET /jr/terminal):"), term);
  const refreshTerminal = async () => { term.textContent = await (await fetch("/jr/terminal")).text(); };
  const view = new JsonRenderView(web, {
    log: shell.log,
    onAction: async (action, params) => {
      shell.log(`action -> ${action}`, params, "client");
      const ops = await postJSON("/jr/action", { action, params, state: view.spec.state });
      shell.log("patches <-", ops, ops[0]?.error ? "error" : "");
      if (!ops[0]?.error) { view.applyPatches(ops); refreshTerminal(); }
    },
  });
  await postSSE("/jr/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") return shell.log(`rejected ${msg.rejected}`, msg.errors.join("; "), "error");
    shell.log(`${msg.op} ${msg.path}`, msg);
    view.applyPatches([msg]);
  });
  await refreshTerminal();
  shell.setStatus("catalog components + one HtmlBlock · setState runs locally · custom actions go to the server");
}

shell.runButton.addEventListener("click", run);
run();
