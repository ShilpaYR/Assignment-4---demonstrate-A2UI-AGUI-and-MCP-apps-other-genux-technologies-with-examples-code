// AG-UI lab 3 (open-ended): the model writes the whole widget; the page sandboxes it.
import { createShell } from "/common/shell.js";
import { h } from "/common/ui.js";
import { runAgent, newId } from "/common/agui.js";
import { mountSandboxed } from "/common/sandbox.js";

const PROMPT = "Build an interactive break-even calculator for the coffee cart: sliders for price per cup, cost per cup and fixed weekly costs.";
const shell = createShell({ part: "Part 1 · AG-UI", title: "Lab 3 - model-written HTML in a sandbox", mode: "open-ended", prompt: PROMPT });

async function run() {
  shell.clearLog();
  const source = h("pre", { class: "chat", style: "max-height:180px;overflow:auto;font:11px/1.35 var(--mono)" });
  const stage = h("div");
  shell.canvas.replaceChildren(h("div", { class: "status" }, "Model output (raw HTML, streaming):"), source, stage);
  let chars = 0;

  await runAgent("/agui", {
    threadId: "thread_open",
    messages: [{ id: newId("msg"), role: "user", content: PROMPT }],
  }, (ev) => {
    if (!ev.type.startsWith("TEXT_MESSAGE_CONTENT") && ev.type !== "TEXT_MESSAGE_END") shell.log(ev.type, ev);
    switch (ev.type) {
      case "TEXT_MESSAGE_CONTENT":                    // show the source as it arrives; do NOT run it yet
        chars += ev.delta.length;
        source.textContent += ev.delta;
        source.scrollTop = source.scrollHeight;
        shell.setStatus(`streaming HTML ... ${chars} characters`);
        break;
      case "TEXT_MESSAGE_END":
        shell.log("TEXT_MESSAGE_CONTENT x many", `${chars} characters of HTML (collapsed)`);
        shell.log(ev.type, ev);
        break;
      case "ACTIVITY_SNAPSHOT": {
        const a = ev.content;
        if (a.status !== "ready") { stage.append(h("div", { class: "g-error" }, "rejected by policy: " + a.problems.join("; "))); break; }
        const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, a.title), h("span", {}, `sandboxed · ${a.tokens} tokens`)));
        stage.append(box);
        // the only door out of the sandbox: one message shape, one allowed event name
        mountSandboxed(box, a.html, {
          allowed: a.allowedEvents,
          onEvent: (name, payload) => shell.log(`iframe -> page: ${name}`, payload, name === "rejected" ? "error" : "client"),
        });
        break;
      }
      case "RUN_FINISHED": shell.setStatus("run finished: the widget below is model-written code, isolated in a sandboxed iframe"); break;
    }
  });
}

shell.runButton.addEventListener("click", run);
run();
