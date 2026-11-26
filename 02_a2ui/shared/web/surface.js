// A small A2UI v1.0 renderer (a subset of the Basic Catalog + the genux HtmlFrame).
//
// It keeps, per surface: the default catalog, a Map of components (the flat
// list, by id) and the data model. Components bind to the data model with
// {"@path": "/pointer"}; when updateDataModel arrives only the bound nodes
// update (a tiny version of the signals real A2UI renderers use). The page
// never trusts structure it cannot draw: unknown components, unknown catalogs
// and missing children render as visible placeholders.
import { h } from "/common/ui.js";
import { getPointer, setPointer } from "/common/jsonpatch.js";
import { mountSandboxed } from "/common/sandbox.js";

export const BASIC = "https://a2ui.org/specification/v1_0/catalogs/basic/catalog.json";
export const HTML = "https://catalogs.genux.example/html/v1/catalog.json";
const SUPPORTED = new Set([BASIC, HTML]);
const ICONS = { mail: "✉", check: "✔", warning: "⚠", shoppingCart: "🛒", info: "ℹ", star: "★", settings: "⚙" };

// Text supports a little Markdown: "# .. #####" headings and **bold**.
function markdown(text) {
  const s = String(text ?? "");
  const m = s.match(/^(#{1,5})\s+(.*)$/s);
  const bold = (t) => t.split(/\*\*(.+?)\*\*/g).map((part, i) => (i % 2 ? h("strong", {}, part) : part));
  return m ? h(`h${m[1].length + 1}`, { class: "a2-h" }, bold(m[2])) : h("span", {}, bold(s));
}

export class A2uiRenderer {
  constructor(container, { onAction, log } = {}) {
    this.container = container;
    this.onAction = onAction;
    this.log = log || (() => {});
    this.surfaces = new Map();
  }

  // ---- the four agent-to-renderer messages --------------------------------
  process(msg) {
    if (msg.version !== "1.0") return this.log("rejected (version)", msg, "error");
    if (msg.createSurface) {
      const { surfaceId, catalogId, components, dataModel } = msg.createSurface;
      if (this.surfaces.has(surfaceId)) return this.log("error: surface exists", surfaceId, "error");
      const el = h("div", { class: "a2-surface", "data-surface": surfaceId });
      this.container.append(el);
      this.surfaces.set(surfaceId, { id: surfaceId, catalogId, components: new Map(), data: dataModel || {}, el, bindings: [] });
      if (components) this.process({ version: "1.0", updateComponents: { surfaceId, components } });
      else this.render(surfaceId);
    } else if (msg.updateComponents) {
      const s = this.surfaces.get(msg.updateComponents.surfaceId);
      for (const c of msg.updateComponents.components) s.components.set(c.id, c);
      // While the surface is still incomplete, re-render it all. Afterwards, re-render only the
      // updated components, so a sandboxed HtmlFrame elsewhere on the surface keeps its state.
      if (!s.el.querySelector("[data-id=root]") || s.el.querySelector(".g-skeleton")) this.render(s.id);
      else for (const c of msg.updateComponents.components) s.el.querySelectorAll(`[data-id="${c.id}"]`).forEach((old) => old.replaceWith(this.node(s, c.id, "")));
    } else if (msg.updateDataModel) {
      const { surfaceId, path, value } = msg.updateDataModel;
      const s = this.surfaces.get(surfaceId);
      if (value === null) { const parent = path.split("/").slice(0, -1).join("/"); const p = getPointer(s.data, parent); if (p) delete p[path.split("/").pop()]; }
      else s.data = setPointer(s.data, path, structuredClone(value));
      this.refresh(s, path);
    } else if (msg.deleteSurface) {
      const s = this.surfaces.get(msg.deleteSurface.surfaceId);
      s?.el.remove();
      this.surfaces.delete(msg.deleteSurface.surfaceId);
    }
  }

  // ---- data binding ---------------------------------------------------------
  abs(path, scope) { return path.startsWith("/") ? path : `${scope || ""}/${path}`; }

  resolve(s, value, scope, onChange) {
    if (value && typeof value === "object" && "@path" in value) {
      const path = this.abs(value["@path"], scope);
      if (onChange) s.bindings.push({ path, update: () => onChange(getPointer(s.data, path)) });
      return getPointer(s.data, path);
    }
    if (value && typeof value === "object" && value["@call"] === "formatString") {
      // basic-catalog function: "Beans: ${/inventory/beans_kg} kg" (absolute or template-relative paths)
      const template = String(value.args?.value ?? "");
      const paths = [...template.matchAll(/\$\{([^}]+)\}/g)].map((m) => this.abs(m[1].trim(), scope));
      const fmt = () => template.replace(/\$\{([^}]+)\}/g, (_, p) => String(getPointer(s.data, this.abs(p.trim(), scope)) ?? ""));
      if (onChange) for (const path of paths) s.bindings.push({ path, update: () => onChange(fmt()) });
      return fmt();
    }
    if (value && typeof value === "object" && "@call" in value) return `[${value["@call"]}]`; // other functions: not in this subset
    return value;
  }

  refresh(s, changed) {             // run only the bindings under (or above) the changed path
    for (const b of s.bindings) if (b.path.startsWith(changed) || changed.startsWith(b.path)) b.update();
  }

  // ---- rendering --------------------------------------------------------------
  render(surfaceId) {
    const s = this.surfaces.get(surfaceId);
    s.bindings = [];
    s.el.replaceChildren(this.node(s, "root", ""));
  }

  children(s, spec, scope) {
    if (Array.isArray(spec)) return spec.map((id) => this.node(s, id, scope));
    if (spec && typeof spec === "object") {          // template: one child per item in a data list
      const box = h("div", { class: "a2-template" });
      const fill = () => {
        const items = getPointer(s.data, this.abs(spec.path, scope)) || [];
        box.replaceChildren(...items.map((_, i) => this.node(s, spec.componentId, `${this.abs(spec.path, scope)}/${i}`)));
      };
      s.bindings.push({ path: this.abs(spec.path, scope), update: fill });
      fill();
      return [box];
    }
    return [];
  }

  node(s, id, scope) {
    const c = s.components.get(id);
    if (!c) return h("div", { class: "g-skeleton" }, `waiting for component "${id}" ...`);
    const catalog = c["@catalogId"] || s.catalogId;
    if (!SUPPORTED.has(catalog)) return h("div", { class: "g-error" }, `catalog not supported: ${catalog}`);
    const make = (catalog === HTML ? HTML_COMPONENTS : BASIC_COMPONENTS)[c.component];
    if (!make) return h("div", { class: "g-error" }, `unknown component ${c.component} in ${catalog}`);
    const el = make.call(this, s, c, scope);
    el.dataset.id = id;
    return el;
  }

  text(s, value, scope, render) {   // a bound text node that updates itself
    const slot = h("span");
    const paint = (v) => slot.replaceChildren(render ? render(v) : String(v ?? ""));
    paint(this.resolve(s, value, scope, paint));
    return slot;
  }

  // ---- actions: renderer -> agent ---------------------------------------------
  fire(s, sourceComponentId, name, context, scope) {
    const resolved = {};
    for (const [k, v] of Object.entries(context || {})) resolved[k] = this.resolve(s, v, scope);
    const msg = { version: "1.0", action: { name, surfaceId: s.id, sourceComponentId, timestamp: new Date().toISOString(), context: resolved } };
    this.onAction?.(msg);
  }
}

const BASIC_COMPONENTS = {
  Text(s, c, scope) { return h("div", { class: `g-text a2-text ${c.variant === "caption" ? "muted" : ""}` }, this.text(s, c.text, scope, markdown)); },
  Column(s, c, scope) { return h("div", { class: "g-col" }, this.children(s, c.children, scope)); },
  Row(s, c, scope) { return h("div", { class: "g-row" }, this.children(s, c.children, scope)); },
  List(s, c, scope) { return h("div", { class: c.direction === "horizontal" ? "g-row" : "g-col a2-list" }, this.children(s, c.children, scope)); },
  Card(s, c, scope) { return h("div", { class: "g-card" }, this.node(s, c.child, scope)); },
  Divider() { return h("hr", { class: "a2-divider" }); },
  Icon(s, c) { return h("span", { class: "a2-icon" }, ICONS[c.name] || "•"); },
  Button(s, c, scope) {
    const ev = c.action?.event;
    return h("button", { class: `g-button ${c.variant === "borderless" ? "secondary" : ""}`, "data-action": ev?.name,
      onClick: () => ev && this.fire(s, c.id, ev.name, ev.context, scope) }, this.node(s, c.child, scope));
  },
  TextField(s, c, scope) {          // two-way binding: typing writes into the data model
    const path = c.value?.["@path"] && this.abs(c.value["@path"], scope);
    const input = h("input", { type: c.variant === "number" ? "number" : "text", placeholder: this.resolve(s, c.placeholder, scope) || "", "data-bind": path });
    input.value = this.resolve(s, c.value, scope, (v) => { if (document.activeElement !== input) input.value = v ?? ""; }) ?? "";
    input.addEventListener("input", () => { if (path) s.data = setPointer(s.data, path, c.variant === "number" ? Number(input.value) : input.value); });
    return h("label", { class: "g-field" }, this.text(s, c.label, scope), input);
  },
  CheckBox(s, c, scope) {
    const path = c.value?.["@path"] && this.abs(c.value["@path"], scope);
    const box = h("input", { type: "checkbox", "data-bind": path });
    box.checked = !!this.resolve(s, c.value, scope, (v) => { box.checked = !!v; });
    box.addEventListener("change", () => { if (path) s.data = setPointer(s.data, path, box.checked); });
    return h("label", { class: "g-check" }, box, this.text(s, c.label, scope));
  },
  Slider(s, c, scope) {
    const path = c.value?.["@path"] && this.abs(c.value["@path"], scope);
    const out = h("output");
    const input = h("input", { type: "range", min: c.min ?? 0, max: c.max, step: c.steps ? (c.max - (c.min ?? 0)) / c.steps : "any", "data-bind": path });
    input.value = this.resolve(s, c.value, scope, (v) => { input.value = v; out.textContent = v; });
    out.textContent = input.value;
    input.addEventListener("input", () => { out.textContent = input.value; if (path) s.data = setPointer(s.data, path, Number(input.value)); });
    return h("label", { class: "g-field" }, this.text(s, c.label, scope), h("div", { class: "g-row" }, input, out));
  },
};

const HTML_COMPONENTS = {
  HtmlFrame(s, c, scope) {          // open-ended region: sandboxed, events become A2UI actions
    const box = h("div", { class: "g-generated" },
      h("div", { class: "gtitle" }, this.text(s, c.title || "Generated view", scope), h("span", {}, "HtmlFrame · sandboxed")));
    mountSandboxed(box, c.html, {
      allowed: c.allowedEvents,
      onEvent: (name, payload) => {
        if (name === "rejected") return this.log("dropped iframe event", payload, "error");
        this.log(`iframe -> renderer: ${name}`, payload, "client");
        this.fire(s, c.id, name, Object.fromEntries(Object.entries(payload || {}).map(([k, v]) => [k, v])), scope);
      },
    });
    if (c.caption) box.append(h("div", { class: "g-text muted", style: "margin-top:6px" }, this.text(s, c.caption, scope)));
    return box;
  },
};
