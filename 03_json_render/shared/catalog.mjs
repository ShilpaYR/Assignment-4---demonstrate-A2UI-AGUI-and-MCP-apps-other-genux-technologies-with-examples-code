// The json-render catalogs for Part 3, defined with the official library.
//
// One definition, three uses (the json-render promise):
//   1. catalog.prompt()     -> the system prompt          (generated/prompt_*.txt)
//   2. catalog.jsonSchema() -> the validator              (generated/schema_*.json, used by Python)
//   3. the component names  -> the renderer registry      (web/jr-render.js)
import { z } from "zod";
import { defineCatalog } from "@json-render/core";
import { schema } from "@json-render/react/schema";

const components = {
  Card: { props: z.object({ title: z.string(), subtitle: z.string().nullable() }), description: "A titled container; children go inside." },
  Row: { props: z.object({}), description: "Lays its children out side by side." },
  Column: { props: z.object({}), description: "Stacks its children vertically." },
  Text: { props: z.object({ text: z.string(), tone: z.enum(["normal", "muted", "strong"]).nullable() }), description: "One paragraph of text." },
  Metric: { props: z.object({ label: z.string(), value: z.string(), delta: z.string().nullable() }), description: "One key number with a label and an optional change such as '+8%'." },
  BarChart: { props: z.object({ title: z.string().nullable(), labels: z.array(z.string()), values: z.array(z.number()) }), description: "A bar chart; labels and values have the same length." },
  Table: { props: z.object({ columns: z.array(z.string()), rows: z.array(z.array(z.string())) }), description: "A table; every row has one cell per column." },
  Button: { props: z.object({ label: z.string() }), description: "A button. Put what it does in the element's on.press binding." },
};

const HtmlBlock = {
  props: z.object({ title: z.string(), html: z.string(), caption: z.string().nullable() }),
  description: "A sandboxed region of model-written HTML/CSS/JS. Use only for what the other components cannot express. " +
    "Inside the document, genux.emit(name, payload) fires the element's on[name] binding.",
};

const actions = {
  restock_beans: { description: "Order more coffee beans. params: { kg: number }" },
  apply_price: { description: "Use a new list price per cup. params: { price: number }" },
};

export const catalog = defineCatalog(schema, { components, actions });
export const hybridCatalog = defineCatalog(schema, { components: { ...components, HtmlBlock }, actions });
export const htmlCatalog = defineCatalog(schema, { components: { HtmlBlock }, actions: { apply_price: actions.apply_price } });
export const CATALOGS = { base: catalog, hybrid: hybridCatalog, html: htmlCatalog };
