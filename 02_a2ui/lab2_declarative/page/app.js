// A2UI lab 2 (declarative): the model writes the whole surface; invalid output is retried.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { A2uiRenderer } from "/a2ui/surface.js";

const PROMPT = "Show this week's dashboard for the Campus Coffee Cart and a form to order beans.";
const shell = createShell({ part: "Part 2 · A2UI", title: "Lab 2 - model-written surface, validated and corrected", mode: "declarative", prompt: PROMPT });
const kindOf = (m) => Object.keys(m).find((k) => k !== "version");

async function run() {
  shell.clearLog();
  shell.canvas.textContent = "";
  const renderer = new A2uiRenderer(shell.canvas, {
    log: shell.log,
    onAction: async (msg) => {                       // the form's values travel inside the action context
      shell.log("action ->", msg, "client");
      for (const reply of await postJSON("/a2ui/action", msg)) { shell.log(`${kindOf(reply)} <-`, reply); renderer.process(reply); }
    },
  });
  await postSSE("/a2ui/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {                          // validation report for one attempt
      shell.log(`attempt ${msg.attempt}: ${msg.valid ? "valid" : "INVALID"}`, msg.valid ? "accepted by the A2UI v1.0 schema" : msg.errors.join("\n"), msg.valid ? "ok" : "error");
      shell.setStatus(msg.valid ? `attempt ${msg.attempt} valid - streaming the surface` : `attempt ${msg.attempt} rejected - errors sent back to the model`);
      return;
    }
    shell.log(kindOf(msg), msg);
    renderer.process(msg);
  });
  shell.setStatus("done: the layout was written by the model, checked against the official schema, then rendered");
}

shell.runButton.addEventListener("click", run);
run();
