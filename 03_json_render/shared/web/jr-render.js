// A json-render spec renderer in plain DOM (the official one is @json-render/react).
//
// spec = { root, elements: { id: { type, props, children, visible?, on? } }, state }
//   - props may hold expressions: {"$state": "/p"}, {"$bindState": "/p"}, {"$cond": ..., "$then": ..., "$else": ...}
//   - "visible" hides an element unless its condition holds
//   - "on": { press: { action, params } } binds an event to an action;
//     setState is built in (runs locally); every other action goes to the server.
// The renderer records which state paths each element read, so a state change
// re-renders only the elements that depend on it.
import { h, components } from "/common/ui.js";
import { applyPatch, getPointer, setPointer } from "/common/jsonpatch.js";
import { mountSandboxed } from "/common/sandbox.js";

const BUILTIN = new Set(["setState"]);

export class JsonRenderView {
  constructor(container, { onAction, log } = {}) {
    this.container = container;
    this.onAction = onAction;
    this.log = log || (() => {});
    this.spec = { root: null, elements: {}, state: {} };
    this.deps = new Map();          // element id -> Set(state paths it read)
    this.live = [];                 // in-place text updaters (HtmlBlock captions)
  }

  // ---- input: a whole spec, or SpecStream patches ---------------------------
  setSpec(spec) { this.spec = structuredClone(spec); this.spec.state ??= {}; this.render(); }

  applyPatches(ops) {
    this.spec = applyPatch(this.spec, ops);
    this.spec.state ??= {};
    const structural = ops.some((op) => !op.path.startsWith("/state"));
    if (structural) this.render();
    else this.stateChanged(ops.map((op) => op.path.slice("/state".length) || "/"));
  }

  // ---- expressions ------------------------------------------------------------
  read(id, path) { this.deps.get(id)?.add(path); return getPointer(this.spec.state, path); }

  test(id, cond) {                  // visibility / $cond conditions
    if (typeof cond === "boolean") return cond;
    if (cond && "$state" in cond) {
      const v = this.read(id, cond.$state);
      if ("eq" in cond) return v === cond.eq;
      if ("neq" in cond) return v !== cond.neq;
      return cond.not ? !v : !!v;
    }
    return true;
  }

  value(id, v) {
    if (v && typeof v === "object" && !Array.isArray(v)) {
      if ("$state" in v) return this.read(id, v.$state);
      if ("$bindState" in v) return this.read(id, v.$bindState);
      if ("$cond" in v) return this.test(id, v.$cond) ? this.value(id, v.$then) : this.value(id, v.$else);
    }
    return v;
  }

  props(id, el) { return Object.fromEntries(Object.entries(el.props || {}).map(([k, v]) => [k, this.value(id, v)])); }

  // ---- events and actions -----------------------------------------------------
  async fire(id, event, payload = {}) {
    const bindings = [].concat(this.spec.elements[id]?.on?.[event] || []);
    for (const b of bindings) {
      const params = { ...Object.fromEntries(Object.entries(b.params || {}).map(([k, v]) => [k, this.value(id, v)])), ...payload };
      if (BUILTIN.has(b.action)) {                    // built-in: change state locally, no server round trip
        this.log("setState (local)", params, "ok");
        this.spec.state = setPointer(this.spec.state, params.statePath, params.value);
        this.stateChanged([params.statePath]);
      } else {
        await this.onAction?.(b.action, params, id);  // custom: the application decides
      }
    }
  }

  // ---- rendering ----------------------------------------------------------------
  render() {
    this.deps.clear();
    this.live = [];
    this.container.replaceChildren(this.node(this.spec.root));
  }

  stateChanged(paths) {
    const hit = (deps) => [...deps].some((d) => paths.some((p) => d.startsWith(p) || p.startsWith(d)));
    for (const u of this.live) if (paths.some((p) => u.path.startsWith(p) || p.startsWith(u.path))) u.update();
    for (const [id, deps] of [...this.deps]) {
      if (!hit(deps) || this.spec.elements[id]?.type === "HtmlBlock") continue;
      this.container.querySelectorAll(`[data-id="${id}"]`).forEach((old) => old.replaceWith(this.node(id)));
    }
  }

  node(id) {
    const el = id && this.spec.elements[id];
    if (!el) return h("div", { class: "g-skeleton" }, `waiting for "${id ?? "root"}" ...`);
    this.deps.set(id, new Set());
    let out;
    if (el.visible !== undefined && !this.test(id, el.visible)) out = h("div", { hidden: true });
    else if (el.type === "Button") {
      out = h("button", { class: "g-button", "data-action": [].concat(el.on?.press || [])[0]?.action, onClick: () => this.fire(id, "press") }, this.props(id, el).label);
    } else if (el.type === "HtmlBlock") out = this.htmlBlock(id, el);
    else {
      const make = components[el.type];
      out = make ? make(this.props(id, el), (el.children || []).map((c) => this.node(c)), {}) : h("div", { class: "g-error" }, `unknown component ${el.type}`);
    }
    out.dataset.id = id;
    return out;
  }

  htmlBlock(id, el) {
    const p = this.props(id, el);
    const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, p.title), h("span", {}, "HtmlBlock · sandboxed")));
    if (p.html) {
      mountSandboxed(box, p.html, {
        allowed: Object.keys(el.on || {}),           // only events the spec binds may leave the frame
        onEvent: (name, payload) => {
          if (name === "rejected") return this.log("dropped iframe event", payload, "error");
          this.log(`iframe -> ${name}`, payload, "client");
          this.fire(id, name, payload);
        },
      });
    } else box.append(h("div", { class: "g-skeleton" }, "generating ..."));
    const caption = el.props?.caption;
    if (caption) {                                    // updated in place: the iframe is never re-created
      const span = h("div", { class: "g-text muted", style: "margin-top:6px" });
      const update = () => { span.textContent = this.value(id, caption) ?? ""; };
      if (caption.$state) this.live.push({ path: caption.$state, update });
      update();
      box.append(span);
    }
    return box;
  }
}
