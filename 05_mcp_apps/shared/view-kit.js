var GenuxUI = (() => {
  var __defProp = Object.defineProperty;
  var __getOwnPropDesc = Object.getOwnPropertyDescriptor;
  var __getOwnPropNames = Object.getOwnPropertyNames;
  var __hasOwnProp = Object.prototype.hasOwnProperty;
  var __export = (target, all) => {
    for (var name in all)
      __defProp(target, name, { get: all[name], enumerable: true });
  };
  var __copyProps = (to, from, except, desc) => {
    if (from && typeof from === "object" || typeof from === "function") {
      for (let key of __getOwnPropNames(from))
        if (!__hasOwnProp.call(to, key) && key !== except)
          __defProp(to, key, { get: () => from[key], enumerable: !(desc = __getOwnPropDesc(from, key)) || desc.enumerable });
    }
    return to;
  };
  var __toCommonJS = (mod) => __copyProps(__defProp({}, "__esModule", { value: true }), mod);

  // 05_mcp_apps/shared/view-kit-entry.js
  var view_kit_entry_exports = {};
  __export(view_kit_entry_exports, {
    applyPatch: () => applyPatch,
    components: () => components,
    h: () => h,
    mountSandboxed: () => mountSandboxed,
    renderSpec: () => renderSpec,
    wrapDocument: () => wrapDocument
  });

  // common/web/sandbox.js
  var CSP = "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'";
  var BRIDGE = `<script>
window.genux = { emit: function (name, payload) {
  parent.postMessage({ type: "genux:event", name: String(name), payload: payload === undefined ? null : payload }, "*"); } };
addEventListener("load", function () {
  new ResizeObserver(function () {
    parent.postMessage({ type: "genux:resize", height: Math.ceil(document.body.getBoundingClientRect().bottom) + 16 }, "*");
  }).observe(document.body);
});
<\/script>`;
  function wrapDocument(html, csp = CSP) {
    const meta = `<meta http-equiv="Content-Security-Policy" content="${csp}">`;
    let doc = String(html);
    if (/<head[^>]*>/i.test(doc)) doc = doc.replace(/<head[^>]*>/i, (m) => m + meta + BRIDGE);
    else if (/<html[^>]*>/i.test(doc)) doc = doc.replace(/<html[^>]*>/i, (m) => `${m}<head>${meta}${BRIDGE}</head>`);
    else doc = `<!doctype html><html><head>${meta}${BRIDGE}</head><body>${doc}</body></html>`;
    return doc;
  }
  function mountSandboxed(container, html, { onEvent, allowed, height = 320 } = {}) {
    const frame = document.createElement("iframe");
    frame.className = "genux-sandbox";
    frame.setAttribute("sandbox", "allow-scripts");
    frame.setAttribute("referrerpolicy", "no-referrer");
    frame.style.height = `${height}px`;
    frame.srcdoc = wrapDocument(html);
    const listener = (e) => {
      if (e.source !== frame.contentWindow) return;
      const d = e.data;
      if (!d || typeof d !== "object") return;
      if (d.type === "genux:resize" && Number.isFinite(d.height)) {
        frame.style.height = `${Math.min(900, Math.max(80, d.height + 4))}px`;
        return;
      }
      if (d.type !== "genux:event" || typeof d.name !== "string") return;
      if (allowed && !allowed.includes(d.name)) {
        onEvent?.("rejected", { name: d.name });
        return;
      }
      onEvent?.(d.name, d.payload);
    };
    window.addEventListener("message", listener);
    container.append(frame);
    return { frame, dispose() {
      window.removeEventListener("message", listener);
      frame.remove();
    } };
  }

  // common/web/ui.js
  function h(tag, attrs = {}, ...children) {
    const el = document.createElement(tag);
    for (const [k, v] of Object.entries(attrs || {})) {
      if (v === void 0 || v === null || v === false) continue;
      if (k.startsWith("on") && typeof v === "function") el.addEventListener(k.slice(2).toLowerCase(), v);
      else if (k === "class") el.className = v;
      else el.setAttribute(k, v === true ? "" : String(v));
    }
    for (const c of children.flat()) {
      if (c === null || c === void 0 || c === false) continue;
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
      const bh = (H - pad) * v / max;
      const rect = document.createElementNS(ns, "rect");
      Object.entries({ x: pad + i * bw + 4, y: H - bh, width: bw - 8, height: bh, rx: 3, fill: "#7a4b2a" }).forEach(([k, val]) => rect.setAttribute(k, val));
      const label = document.createElementNS(ns, "text");
      Object.entries({ x: pad + i * bw + bw / 2, y: H + 14, "text-anchor": "middle", "font-size": 11, fill: "#6c675c" }).forEach(([k, val]) => label.setAttribute(k, val));
      label.textContent = labels[i] ?? "";
      const tip = document.createElementNS(ns, "title");
      tip.textContent = `${labels[i]}: ${v}`;
      rect.append(tip);
      svg.append(rect, label);
    });
    return h("div", { class: "g-chart" }, title ? h("div", { class: "title" }, title) : null, svg);
  }
  var components = {
    Card: (p, kids) => h("div", { class: "g-card" }, h("h2", {}, p.title), p.subtitle ? h("div", { class: "sub" }, p.subtitle) : null, kids),
    Row: (p, kids) => h("div", { class: "g-row" }, kids),
    Column: (p, kids) => h("div", { class: "g-col" }, kids),
    Text: (p) => h("p", { class: `g-text ${p.tone || ""}` }, p.text),
    Metric: (p) => h(
      "div",
      { class: "g-metric" },
      h("div", { class: "label" }, p.label),
      h("div", { class: "value" }, p.value),
      p.delta ? h("div", { class: `delta ${String(p.delta).startsWith("-") ? "neg" : ""}` }, p.delta) : null
    ),
    BarChart: (p) => barChart(p),
    Table: (p) => h(
      "table",
      { class: "g-table" },
      h("thead", {}, h("tr", {}, (p.columns || []).map((c) => h("th", {}, c)))),
      h("tbody", {}, (p.rows || []).map((r) => h("tr", {}, r.map((c) => h("td", {}, c)))))
    ),
    Button: (p, kids, ctx) => h("button", {
      class: "g-button",
      "data-action": p.action,
      onClick: () => ctx.onAction?.(p.action, p.params || {})
    }, p.label),
    GeneratedView: (p, kids, ctx) => {
      const box = h("div", { class: "g-generated" }, h("div", { class: "gtitle" }, h("span", {}, p.title || "Generated view"), h("span", {}, "sandboxed")));
      if (p.html) mountSandboxed(box, p.html, { onEvent: ctx.onGeneratedEvent, allowed: ctx.allowedEvents });
      else box.append(h("div", { class: "g-skeleton" }, "generating ..."));
      return box;
    }
  };
  var skeleton = (id) => h("div", { class: "g-skeleton", "data-pending": id }, `waiting for "${id}" ...`);
  var errorBox = (msg) => h("div", { class: "g-error" }, msg);
  function renderSpec(spec, ctx = {}) {
    if (!spec || !spec.root) return skeleton("root");
    const resolve = ctx.resolveProps || ((p) => p);
    const seen = /* @__PURE__ */ new Set();
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

  // common/web/jsonpatch.js
  var tokens = (ptr) => ptr === "" || ptr === "/" ? [] : ptr.slice(1).split("/").map((t) => t.replace(/~1/g, "/").replace(/~0/g, "~"));
  function getPointer(doc, ptr) {
    let cur = doc;
    for (const t of tokens(ptr)) {
      if (cur == null) return void 0;
      cur = cur[Array.isArray(cur) ? Number(t) : t];
    }
    return cur;
  }
  function applyPatch(doc, ops) {
    let out = structuredClone(doc ?? {});
    for (const op of ops) {
      const toks = tokens(op.path);
      if (!toks.length) {
        if (op.op === "add" || op.op === "replace") out = structuredClone(op.value);
        continue;
      }
      let parent = out;
      for (const t of toks.slice(0, -1)) {
        if (parent[t] === void 0) parent[t] = {};
        parent = parent[t];
      }
      const key = toks.at(-1);
      if (op.op === "add" || op.op === "replace") {
        if (Array.isArray(parent)) {
          const i = key === "-" ? parent.length : Number(key);
          op.op === "add" ? parent.splice(i, 0, structuredClone(op.value)) : parent[i] = structuredClone(op.value);
        } else parent[key] = structuredClone(op.value);
      } else if (op.op === "remove") {
        Array.isArray(parent) ? parent.splice(Number(key), 1) : delete parent[key];
      } else if (op.op === "test") {
        if (JSON.stringify(getPointer(out, op.path)) !== JSON.stringify(op.value)) throw new Error(`test failed at ${op.path}`);
      } else throw new Error(`unsupported op ${op.op}`);
    }
    return out;
  }
  return __toCommonJS(view_kit_entry_exports);
})();
