// Hand-written, pre-built components. Every lab draws with these, whatever the
// format (AG-UI state, A2UI surface, json-render spec, OpenUI program ...).
// The format decides WHICH components appear and with WHAT props; these
// functions decide how they look. That split is the heart of generative UI.
import { mountSandboxed } from "./sandbox.js";

export function h(tag, attrs = {}, ...children) {
  const el = document.createElement(tag);
  for (const [k, v] of Object.entries(attrs || {})) {
    if (v === undefined || v === null || v === false) continue;
    if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
    else if (k === "class") el.className = v;
    else el.setAttribute(k, v === true ? "" : String(v));
  }
  for (const c of children.flat()) {
    if (c === null || c === undefined || c === false) continue;
    el.append(c instanceof Node ? c : document.createTextNode(String(c)));
  }
  return el;
}

function barChart({ title, labels = [], values = [] }) {
  const W = 420, H = 150, pad = 22, max = Math.max(1, ...values);
  const bw = (W - pad * 2) / Math.max(1, values.length);
  const ns = "http://www.w3.org/2000/svg";
  const svg = document.createElementNS(ns, "svg");
  svg.setAttribute("viewBox", `0 0 ${W} ${H + 18}`);
  svg.setAttribute("width", "100%");
  svg.setAttribute("height", "180");
  values.forEach((v, i) => {
    const bh = ((H - pad) * v) / max;
    const rect = document.createElementNS(ns, "rect");
    Object.entries({ x: pad + i * bw + 4, y: H - bh, width: bw - 8, height: bh, rx: 3, fill: "#7a4b2a" })
      .forEach(([k, val]) => rect.setAttribute(k, val));
    const label = document.createElementNS(ns, "text");
    Object.entries({ x: pad + i * bw + bw / 2, y: H + 14, "text-anchor": "middle", "font-size": 11, fill: "#6c675c" })
      .forEach(([k, val]) => label.setAttribute(k, val));
    label.textContent = labels[i] ?? "";
    const tip = document.createElementNS(ns, "title");
    tip.textContent = `${labels[i]}: ${v}`;
    rect.append(tip);
    svg.append(rect, label);
  });
  return h("div", { class: "g-chart" }, title ? h("div", { class: "title" }, title) : null, svg);
}

// name -> (props, children[], ctx) => Node
export const components = {
  Card: (p, kids) => h("div", { class: "g-card" }, h("h2", {}, p.title), p.subtitle ? h("div", { class: "sub" }, p.subtitle) : null, kids),
  Row: (p, kids) => h("div", { class: "g-row" }, kids),
  Column: (p, kids) => h("div", { class: "g-col" }, kids),
  Text: (p) => h("p", { class: `g-text ${p.tone || ""}` }, p.text),
  Metric: (p) => h("div", { class: "g-metric" },
    h("div", { class: "label" }, p.label), h("div", { class: "value" }, p.value),
    p.delta ? h("div", { class: `delta ${String(p.delta).startsWith("-") ? "neg" : ""}` }, p.delta) : null),
  BarChart: (p) => barChart(p),
  Table: (p) => h("table", { class: "g-table" },
    h("thead", {}, h("tr", {}, (p.columns || []).map((c) => h("th", {}, c)))),
    h("tbody", {}, (p.rows || []).map((r) => h("tr", {}, r.map((c) => h("td", {}, c)))))),
  Button: (p, kids, ctx) => h("button", {
    class: "g-button", "data-action": p.action,
    onClick: () => ctx.onAction?.(p.action, p.params || {}),
  }, p.label),
  GeneratedView: (p, kids, ctx) => {
    const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, p.title || "Generated view"), h("span", {}, "sandboxed")));
    if (p.html) mountSandboxed(box, p.html, { onEvent: ctx.onGeneratedEvent, allowed: ctx.allowedEvents });
    else box.append(h("div", { class: "g-skeleton" }, "generating ..."));
    return box;
  },
};

export const skeleton = (id) => h("div", { class: "g-skeleton", "data-pending": id }, `waiting for "${id}" ...`);
export const errorBox = (msg) => h("div", { class: "g-error" }, msg);

// Render a flat element map { root, elements: { id: { type, props, children } } }.
// A child id that has not arrived yet becomes a skeleton: that is what lets a
// streamed spec paint before it is complete.
export function renderSpec(spec, ctx = {}) {
  if (!spec || !spec.root) return skeleton("root");
  const resolve = ctx.resolveProps || ((p) => p);
  const seen = new Set();
  const visit = (id) => {
    const el = spec.elements?.[id];
    if (!el) return skeleton(id);
    if (seen.has(id)) return errorBox(`cycle at ${id}`);
    seen.add(id);
    const make = components[el.type];
    if (!make) return errorBox(`unknown component ${el.type}`);
    const kids = (el.children || []).map(visit);
    const node = make(resolve(el.props || {}, id), kids, ctx);
    node.dataset.id = id;
    return node;
  };
  return visit(spec.root);
}
