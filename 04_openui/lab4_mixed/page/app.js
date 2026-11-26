// OpenUI lab 4 (mixed): primitives + one HtmlArtifact; user events come back as OpenUI edits.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { OpenUiView } from "/oui/web/oui-render.js";

const PROMPT = "Show this week's dashboard, and add an interactive what-if price calculator that the standard components cannot express.";
const shell = createShell({ part: "Part 4 · OpenUI Lang", title: "Lab 4 - primitives + HtmlArtifact, edits merged by statement", mode: "mixed", prompt: PROMPT });

async function run() {
  shell.clearLog();
  let text = "";
  const view = await new OpenUiView(shell.canvas, {
    library: "hybrid", log: shell.log,
    onAction: async (action, params) => {               // a Button OR an event from inside the artifact
      shell.log(`action -> ${action}`, params, "client");
      const reply = await postJSON("/oui/action", { action, params });
      if (reply.error) return shell.log("refused <-", reply.error, "error");
      shell.log("edit <- (new statements)", reply.patch);
      view.edit(reply.patch);                           // only the changed statement re-renders
    },
  }).init();
  let chunks = 0;
  await postSSE("/oui/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {
      shell.log(`${chunks} chunks of OpenUI Lang (collapsed)`, text.slice(0, 200) + " ...");
      shell.log("official parser + HTML policy", msg, msg.errors.length ? "error" : "ok");
      const share = Math.round((100 * msg.artifact_tokens) / msg.tokens);
      return shell.setStatus(`done: ${msg.statements} statements · ${msg.tokens} tokens · the HtmlArtifact is ${share}% of them`);
    }
    chunks += 1;
    text += msg.delta;
    view.set(text);
  });
  view.set(text, true);
}

shell.runButton.addEventListener("click", run);
run();
