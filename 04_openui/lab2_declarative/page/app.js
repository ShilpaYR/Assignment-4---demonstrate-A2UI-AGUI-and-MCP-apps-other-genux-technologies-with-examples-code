// OpenUI lab 2 (declarative): primitives composed by the model; forward references resolve as lines arrive.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { h } from "/common/ui.js";
import { OpenUiView } from "/oui/web/oui-render.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 4 · OpenUI Lang", title: "Lab 2 - primitives, forward references, streaming", mode: "declarative", prompt: PROMPT });

async function run() {
  shell.clearLog();
  const source = h("pre", { class: "chat", style: "font:11px/1.4 var(--mono);max-height:150px;overflow:auto" });
  const stage = h("div");
  shell.canvas.replaceChildren(source, stage);
  let text = "";
  const view = await new OpenUiView(stage, {
    library: "declarative", log: shell.log,
    onAction: async (action, params) => {
      shell.log(`action -> ${action}`, params, "client");
      const { patch } = await postJSON("/oui/action", { action, params });
      shell.log("edit <- (new statements)", patch);
      view.edit(patch);
    },
  }).init();
  await postSSE("/oui/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {
      shell.log("official parser", msg, msg.errors.length ? "error" : "ok");
      return shell.setStatus(`done: ${msg.statements} statements, ${msg.tokens} tokens (${msg.token_method})`);
    }
    text += msg.delta;
    source.textContent = text;
    const result = view.set(text);                       // official streaming parser, re-run on every chunk
    shell.setStatus(`streaming ... ${result.meta.statementCount} statements, pending: ${result.meta.unresolved.join(", ") || "none"}`);
    shell.log("chunk", `${JSON.stringify(msg.delta)}  | unresolved: [${result.meta.unresolved.join(", ")}]`);
  });
  view.set(text, true);
}

shell.runButton.addEventListener("click", run);
run();
