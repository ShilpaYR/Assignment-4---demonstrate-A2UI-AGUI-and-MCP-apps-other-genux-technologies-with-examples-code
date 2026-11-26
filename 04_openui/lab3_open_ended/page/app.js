// OpenUI lab 3 (open-ended): the whole answer is one HtmlArtifact; it is mounted only when complete.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { OpenUiView } from "/oui/web/oui-render.js";

const PROMPT = "Build an interactive break-even calculator for the coffee cart: sliders for price per cup, cost per cup and fixed weekly costs.";
const shell = createShell({ part: "Part 4 · OpenUI Lang", title: "Lab 3 - one HtmlArtifact, mounted only when complete", mode: "open-ended", prompt: PROMPT });

async function run() {
  shell.clearLog();
  let text = "";
  const view = await new OpenUiView(shell.canvas, {
    library: "html", log: shell.log,
    onAction: async (action, params) => {
      const reply = await postJSON("/oui/action", { action, params });
      shell.log(reply.error ? "refused <-" : "server <-", reply, reply.error ? "error" : "ok");
      shell.setStatus(reply.message || reply.error);
    },
  }).init();
  let chunks = 0;
  await postSSE("/oui/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {
      shell.log(`${chunks} chunks of OpenUI Lang (collapsed)`, text.slice(0, 160) + " ...");
      shell.log("official parser + HTML policy", { ...msg }, msg.errors.length ? "error" : "ok");
      return shell.setStatus(`done: ${msg.tokens} tokens, of which ${msg.artifact_tokens} are the HTML document (${msg.token_method})`);
    }
    chunks += 1;
    text += msg.delta;
    const r = view.set(text);                           // HtmlArtifact stays "partial" until its string closes
    shell.setStatus(`streaming ... ${text.length} chars, artifact partial: ${r.root?.props?.children?.[0]?.partial ?? "not started"}`);
  });
  view.set(text, true);
}

shell.runButton.addEventListener("click", run);
run();
