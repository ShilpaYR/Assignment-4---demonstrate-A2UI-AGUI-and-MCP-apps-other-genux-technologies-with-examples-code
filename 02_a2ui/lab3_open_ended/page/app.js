// A2UI lab 3 (open-ended): one HtmlFrame from a custom catalog; its events become A2UI actions.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { A2uiRenderer } from "/a2ui/surface.js";

const PROMPT = "Build an interactive break-even calculator for the coffee cart: sliders for price per cup, cost per cup and fixed weekly costs.";
const shell = createShell({ part: "Part 2 · A2UI", title: "Lab 3 - a custom catalog whose only component is model-written HTML", mode: "open-ended", prompt: PROMPT });

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
  shell.setStatus("the whole surface is one HtmlFrame (custom catalog); events from it travel as A2UI actions");
}

shell.runButton.addEventListener("click", run);
run();
