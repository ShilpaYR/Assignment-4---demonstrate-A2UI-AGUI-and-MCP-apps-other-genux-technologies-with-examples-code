// Check every bridge message our host and views exchanged against the OFFICIAL
// MCP Apps schemas (zod) from @modelcontextprotocol/ext-apps.
//   node conformance.mjs < bridge_log.json      ([{dir, msg}, ...] as recorded in window.__bridgeLog)
import { readFileSync } from "node:fs";
import * as ext from "@modelcontextprotocol/ext-apps";

const BY_METHOD = {
  "ui/initialize": ext.McpUiInitializeRequestSchema,
  "ui/notifications/initialized": ext.McpUiInitializedNotificationSchema,
  "ui/notifications/size-changed": ext.McpUiSizeChangedNotificationSchema,
  "ui/notifications/tool-input": ext.McpUiToolInputNotificationSchema,
  "ui/notifications/tool-result": ext.McpUiToolResultNotificationSchema,
  "ui/message": ext.McpUiMessageRequestSchema,
  "ui/update-model-context": ext.McpUiUpdateModelContextRequestSchema,
};
const log = JSON.parse(readFileSync(0, "utf8"));
const initIds = new Set(log.filter((e) => e.msg.method === "ui/initialize").map((e) => e.msg.id));
const report = { checked: 0, skipped: [], errors: [] };
for (const { dir, msg } of log) {
  let schema = BY_METHOD[msg.method], value = { method: msg.method, ...(msg.params !== undefined ? { params: msg.params } : {}) };
  if (!msg.method && initIds.has(msg.id) && dir === "host->view") { schema = ext.McpUiInitializeResultSchema; value = msg.result; }
  if (!schema) { report.skipped.push(msg.method || `result #${msg.id}`); continue; }   // core MCP (tools/call) and plain results
  const r = schema.safeParse(value);
  report.checked += 1;
  if (!r.success) report.errors.push({ method: msg.method || "ui/initialize result", issues: r.error.issues.map((i) => `${i.path.join("/")}: ${i.message}`) });
}
console.log(JSON.stringify({ ok: report.errors.length === 0, ...report }));
