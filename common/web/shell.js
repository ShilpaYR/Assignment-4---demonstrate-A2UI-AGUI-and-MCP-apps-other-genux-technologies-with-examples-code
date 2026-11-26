// The page frame every lab shares: a header, the prompt, a canvas for the
// generated UI and a "wire" panel that shows every message that travelled
// between agent and page. The wire panel is what makes the protocols visible.
import { h } from "./ui.js";

export function createShell({ part, title, mode, prompt, runLabel = "Run agent" }) {
  document.title = `${part} - ${title}`;
  const runButton = h("button", { id: "run" }, runLabel);
  const status = h("div", { class: "status", id: "status" });
  const canvas = h("div", { class: "canvas-inner", id: "canvas" });
  const wireList = h("div", { id: "wire" });
  document.body.append(
    h("header", { class: "shell" },
      h("div", {}, h("div", { class: "part" }, part), h("h1", {}, title)),
      h("span", { class: `badge ${mode}` }, mode)),
    h("div", { class: "promptbar" }, h("span", { class: "prompt" }, `"${prompt}"`), runButton),
    h("main", { class: "shell" },
      h("section", { class: "canvas" }, status, canvas),
      h("aside", { class: "wire" }, h("h3", {}, "Wire: messages between agent and page"), wireList)),
  );
  let count = 0;
  return {
    canvas, runButton,
    setStatus(text) { status.textContent = text; },
    log(kind, data, cls = "") {
      count += 1;
      const text = typeof data === "string" ? data : JSON.stringify(data);
      const short = text.length > 420 ? text.slice(0, 420) + ` ... (${text.length} chars)` : text;
      wireList.append(h("div", { class: "entry" }, h("span", { class: `kind ${cls}` }, `${count}. ${kind} `), short));
      wireList.parentElement.scrollTop = wireList.parentElement.scrollHeight;
    },
    clearLog() { wireList.textContent = ""; count = 0; },
  };
}
