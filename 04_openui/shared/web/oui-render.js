// Render OpenUI Lang in the browser with the OFFICIAL parser (bundled from @openuidev/lang-core).
//
// The text grows chunk by chunk; on every chunk the streaming parser re-parses
// it and returns an element tree plus meta (unresolved forward references,
// errors). References that are used before they are defined show up as
// "pending" chips until their line arrives. Edits from the server are new
// statements merged with mergeStatements(); only the changed statements are
// re-rendered, so a sandboxed HtmlArtifact elsewhere keeps its state.
import { createParser, createStreamingParser, mergeStatements } from "./vendor/openui-lang-core.js";
import { h, components } from "/common/ui.js";
import { mountSandboxed } from "/common/sandbox.js";

export class OpenUiView {
  constructor(container, { library, onAction, log, renderers = {} }) {
    Object.assign(this, { container, library, onAction, log: log || (() => {}), renderers });
    this.program = "";
    this.artifacts = new Map();   // statementId -> mounted HtmlArtifact element (mounted once, when complete)
  }

  async init() {
    this.schema = await (await fetch(`/oui/generated/schema_${this.library}.json`)).json();
    this.stream = createStreamingParser(this.schema, "Stack");
    return this;
  }

  // ---- streaming: set the whole text so far ---------------------------------
  set(text, complete = false) {
    this.program = text;
    const result = this.stream.set(text, complete);
    this.paint(result);
    return result;
  }

  // ---- edits: merge new statements into the program -------------------------
  edit(patch) {
    this.program = mergeStatements(this.program, patch);
    const result = createParser(this.schema, "Stack").parse(this.program);
    const changed = new Set([...patch.matchAll(/^\s*([A-Za-z_]\w*)\s*=/gm)].map((m) => m[1]));
    const walk = (n, fn) => { if (n?.type === "element") { fn(n); Object.values(n.props).flat().forEach((v) => walk(v, fn)); } };
    walk(result.root, (n) => {
      if (!changed.has(n.statementId)) return;
      this.container.querySelectorAll(`[data-id="${n.statementId}"]`).forEach((old) => old.replaceWith(this.node(n)));
    });
    return result;
  }

  paint(result) {
    const pending = result.meta.unresolved.length
      ? h("div", { class: "g-skeleton" }, `forward references not defined yet: ${result.meta.unresolved.join(", ")}`) : null;
    this.container.replaceChildren(this.node(result.root), pending || "");
  }

  // ---- element tree -> DOM ------------------------------------------------------
  kids(list) { return (list || []).filter((v) => v?.type === "element").map((n) => this.node(n)); }

  node(n) {
    if (!n || n.type !== "element") return h("div", { class: "g-skeleton" }, "waiting for root ...");
    const p = n.props;
    let out;
    if (this.renderers[n.typeName]) out = this.renderers[n.typeName](p, this);       // pre-built (static) components
    else if (n.typeName === "HtmlArtifact") out = this.artifact(n);
    else if (n.typeName === "Stack") out = h("div", { class: "g-col" }, this.kids(p.children));
    else if (n.typeName === "Card") out = components.Card({ title: p.title }, this.kids(p.children));
    else if (n.typeName === "Row") out = components.Row({}, this.kids(p.children));
    else if (n.typeName === "Button") out = h("button", { class: "g-button", "data-action": p.action, onClick: () => this.onAction?.(p.action, {}, n.statementId) }, p.label);
    else if (components[n.typeName]) out = components[n.typeName](p, [], {});
    else out = h("div", { class: "g-error" }, `no renderer for ${n.typeName}`);
    if (n.partial && n.typeName !== "HtmlArtifact") out.classList.add("oui-partial");
    out.dataset.id = n.statementId;
    return out;
  }

  artifact(n) {
    const { title, document } = n.props;
    const known = this.artifacts.get(n.statementId);
    if (known && !n.partial) return known;                    // already mounted: reuse, never reload
    const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, title || "HtmlArtifact"),
      h("span", {}, n.partial ? `streaming ... ${String(document || "").length} chars` : "HtmlArtifact · sandboxed")));
    if (n.partial || !document) {                             // do not run half a document
      box.append(h("div", { class: "g-skeleton" }, "the model is still writing this document"));
      return box;
    }
    mountSandboxed(box, document, {
      onEvent: (name, payload) => { this.log(`iframe -> ${name}`, payload, "client"); this.onAction?.(name, payload, n.statementId); },
    });
    this.artifacts.set(n.statementId, box);
    return box;
  }
}
