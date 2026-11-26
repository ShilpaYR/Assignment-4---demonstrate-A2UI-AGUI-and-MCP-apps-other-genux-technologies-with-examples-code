// Bundled into view-kit.js (an IIFE exposing window.GenuxUI) so that MCP App views - which are
// self-contained HTML documents with no network access - can reuse the course's components.
export { h, components, renderSpec } from "../../common/web/ui.js";
export { mountSandboxed, wrapDocument } from "../../common/web/sandbox.js";
export { applyPatch } from "../../common/web/jsonpatch.js";
