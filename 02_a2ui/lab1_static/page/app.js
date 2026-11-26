// A2UI lab 1 (static): a developer-written surface; the agent only sends data.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { A2uiRenderer } from "/a2ui/surface.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 2 · A2UI", title: "Lab 1 - fixed surface, agent fills the data model", mode: "static", prompt: PROMPT });

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
  shell.setStatus("structure came from the developer's template; every value came from updateDataModel");
}

shell.runButton.addEventListener("click", run);
run();
