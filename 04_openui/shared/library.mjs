// The OpenUI Lang component libraries for Part 4, defined with the official @openuidev/lang-core.
//
// One definition, three uses:
//   library.prompt()       -> the system prompt (generated/prompt_*.txt)
//   library.toJSONSchema() -> the parser's schema (generated/schema_*.json), used in Node AND in the browser
//   component names        -> the renderer (web/oui-render.js)
// Arguments are POSITIONAL in OpenUI Lang: the order of the Zod keys is the order of the arguments.
import { z } from "zod";
import { createLibrary, defineComponent } from "@openuidev/lang-core";

const c = (name, description, shape) => defineComponent({ name, description, props: z.object(shape), component: null });

const Stack = c("Stack", "Root container: stacks its children vertically.", { children: z.array(z.any()) });
const primitives = [
  Stack,
  c("Card", "A titled container.", { title: z.string(), children: z.array(z.any()) }),
  c("Row", "Lays its children out side by side.", { children: z.array(z.any()) }),
  c("Text", "A paragraph. tone: normal | muted | strong.", { text: z.string(), tone: z.enum(["normal", "muted", "strong"]).optional() }),
  c("Metric", "One key number with a label and an optional change such as '+8%'.", { label: z.string(), value: z.string(), delta: z.string().optional() }),
  c("BarChart", "A bar chart; labels and values have the same length.", { title: z.string(), labels: z.array(z.string()), values: z.array(z.number()) }),
  c("Table", "A table; every row has one cell per column.", { columns: z.array(z.string()), rows: z.array(z.array(z.string())) }),
  c("Button", "A button; action is the name of an app action (restock_beans).", { label: z.string(), action: z.string() }),
];

// STATIC: pre-built, high-level components. The model can only pick one and fill its arguments.
const prebuilt = [
  Stack,
  c("SalesDashboard", "The complete pre-built weekly sales dashboard (KPIs, revenue chart, top items).", {
    title: z.string(), revenue: z.string(), revenueDelta: z.string(), cups: z.string(), avgTicket: z.string(),
    days: z.array(z.string()), dailyRevenue: z.array(z.number()), topItems: z.array(z.array(z.string())),
  }),
  c("InventoryCard", "Pre-built stock card with a restock button.", { beansKg: z.number(), reorderKg: z.number() }),
];

// OPEN-ENDED: the escape hatch (OpenUI's own html-artifact pattern).
const HtmlArtifact = c("HtmlArtifact", "A complete, self-contained HTML document (inline CSS/JS, no network) shown in a sandbox. " +
  "Use ONLY when the user asks for something interactive the other components cannot express. Inside it, genux.emit(name, payload) sends an event.",
  { title: z.string(), document: z.string() });

export const LIBRARIES = {
  static: createLibrary({ components: prebuilt, root: "Stack" }),
  declarative: createLibrary({ components: primitives, root: "Stack" }),
  html: createLibrary({ components: [Stack, HtmlArtifact], root: "Stack" }),
  hybrid: createLibrary({ components: [...primitives, HtmlArtifact], root: "Stack" }),
};
