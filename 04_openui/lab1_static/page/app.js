// OpenUI lab 1 (static): the model picks pre-built components; the page decides how they look.
import { createShell } from "/common/shell.js";
import { postSSE, postJSON } from "/common/sse.js";
import { components as C, h } from "/common/ui.js";
import { OpenUiView } from "/oui/web/oui-render.js";

const PROMPT = "Show this week's sales dashboard for the Campus Coffee Cart.";
const shell = createShell({ part: "Part 4 · OpenUI Lang", title: "Lab 1 - a library of pre-built components", mode: "static", prompt: PROMPT });

// The pre-built components: written by the developer, filled by the model's positional arguments.
const PREBUILT = {
  SalesDashboard: (p) => C.Card({ title: p.title, subtitle: "pre-built SalesDashboard" }, [
    C.Row({}, [C.Metric({ label: "Revenue", value: p.revenue, delta: p.revenueDelta }), C.Metric({ label: "Cups sold", value: p.cups }), C.Metric({ label: "Avg ticket", value: p.avgTicket })]),
    C.BarChart({ title: "Revenue by day (USD)", labels: p.days, values: p.dailyRevenue }),
    C.Table({ columns: ["Item", "Cups", "Revenue"], rows: p.topItems || [] }),
  ]),
  InventoryCard: (p, view) => C.Card({ title: "Inventory", subtitle: "pre-built InventoryCard" }, [
    C.Text({ text: `Beans on hand: ${p.beansKg} kg (reorder at ${p.reorderKg} kg)`, tone: p.beansKg < p.reorderKg ? "strong" : "normal" }),
    h("button", { class: "g-button", "data-action": "restock_beans", onClick: () => view.onAction("restock_beans", { kg: 10 }) }, "Reorder 10 kg"),
  ]),
};

async function run() {
  shell.clearLog();
  let text = "";
  const view = await new OpenUiView(shell.canvas, {
    library: "static", renderers: PREBUILT, log: shell.log,
    onAction: async (action, params) => {
      shell.log(`action -> ${action}`, params, "client");
      const { patch } = await postJSON("/oui/action", { action, params });
      shell.log("edit <- (new statements)", patch);
      view.edit(patch);                                  // mergeStatements, then re-render what changed
    },
  }).init();
  await postSSE("/oui/stream", { prompt: PROMPT }, (msg, event) => {
    if (event === "genux") {
      shell.log("official parser", msg, msg.errors.length ? "error" : "ok");
      return shell.setStatus(`${msg.statements} statements · ${msg.tokens} tokens · the model only chose pre-built components`);
    }
    text += msg.delta;
    shell.log("chunk", msg.delta);
    view.set(text);                                      // re-parse the whole text so far
  });
  view.set(text, true);
}

shell.runButton.addEventListener("click", run);
run();
