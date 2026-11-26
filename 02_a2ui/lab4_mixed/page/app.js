// A2UI lab 4 (mixed): two catalogs on one surface; all four message types.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { A2uiRenderer } from "/a2ui/surface.js";

const PROMPT = "Show this week's dashboard, and add an interactive what-if price calculator that the standard components cannot express.";
const shell = createShell({ part: "Part 2 · A2UI", title: "Lab 4 - basic catalog + one HtmlFrame on the same surface", mode: "mixed", prompt: PROMPT });

const kindOf = (m) => Object.keys(m).find((k) => k !== "version");

async function sendAction(renderer, msg) {               // renderer -> agent
  shell.log("action ->", msg, "client");
  for (const reply of await postJSON("/a2ui/action", msg)) {
    shell.log(`${kindOf(reply)} <-`, reply);
    renderer.process(reply);
  }
}

async function run() {
  shell.clearLog();
  shell.canvas.textContent = "";
  const renderer = new A2uiRenderer(shell.canvas, { onAction: (m) => sendAction(renderer, m), log: shell.log });
  await postSSE("/a2ui/stream", { prompt: PROMPT }, (msg) => {   // agent -> renderer, one message per SSE event
    shell.log(kindOf(msg), msg);
    renderer.process(msg);
  });
  shell.setStatus("basic-catalog components plus one HtmlFrame (@catalogId) on the same surface");
}

shell.runButton.addEventListener("click", run);
run();
