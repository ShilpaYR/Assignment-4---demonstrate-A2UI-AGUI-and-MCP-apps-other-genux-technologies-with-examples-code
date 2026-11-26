// Mount model-written HTML safely (the open-ended and mixed modes).
//
//  1. a Content-Security-Policy <meta> goes FIRST in <head>: no network,
//     no external scripts, inline script/style only;
//  2. a two-line bridge gives the document one way out: genux.emit(name, payload);
//  3. the iframe gets sandbox="allow-scripts" and NOT allow-same-origin, so it
//     runs in an opaque origin with no cookies, storage or parent DOM access;
//  4. the parent accepts a message only if it comes from THAT iframe, has the
//     expected shape and (optionally) a name on the allow-list.
export const CSP =
  "default-src 'none'; script-src 'unsafe-inline'; style-src 'unsafe-inline'; " +
  "img-src data:; font-src data:; connect-src 'none'; form-action 'none'; base-uri 'none'";

const BRIDGE = `<script>
window.genux = { emit: function (name, payload) {
  parent.postMessage({ type: "genux:event", name: String(name), payload: payload === undefined ? null : payload }, "*"); } };
addEventListener("load", function () {
  new ResizeObserver(function () {
    parent.postMessage({ type: "genux:resize", height: Math.ceil(document.body.getBoundingClientRect().bottom) + 16 }, "*");
  }).observe(document.body);
});
</script>`;

export function wrapDocument(html, csp = CSP) {
  const meta = `<meta http-equiv="Content-Security-Policy" content="${csp}">`;
  let doc = String(html);
  if (/<head[^>]*>/i.test(doc)) doc = doc.replace(/<head[^>]*>/i, (m) => m + meta + BRIDGE);
  else if (/<html[^>]*>/i.test(doc)) doc = doc.replace(/<html[^>]*>/i, (m) => `${m}<head>${meta}${BRIDGE}</head>`);
  else doc = `<!doctype html><html><head>${meta}${BRIDGE}</head><body>${doc}</body></html>`;
  return doc;
}

export function mountSandboxed(container, html, { onEvent, allowed, height = 320 } = {}) {
  const frame = document.createElement("iframe");
  frame.className = "genux-sandbox";
  frame.setAttribute("sandbox", "allow-scripts");
  frame.setAttribute("referrerpolicy", "no-referrer");
  frame.style.height = `${height}px`;
  frame.srcdoc = wrapDocument(html);
  const listener = (e) => {
    if (e.source !== frame.contentWindow) return; // only this frame
    const d = e.data;
    if (!d || typeof d !== "object") return;
    if (d.type === "genux:resize" && Number.isFinite(d.height)) {
      frame.style.height = `${Math.min(900, Math.max(80, d.height + 4))}px`;
      return;
    }
    if (d.type !== "genux:event" || typeof d.name !== "string") return; // one accepted shape
    if (allowed && !allowed.includes(d.name)) { onEvent?.("rejected", { name: d.name }); return; }
    onEvent?.(d.name, d.payload);
  };
  window.addEventListener("message", listener);
  container.append(frame);
  return { frame, dispose() { window.removeEventListener("message", listener); frame.remove(); } };
}
