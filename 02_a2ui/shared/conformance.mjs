// Feed an A2UI message stream to Google's official renderer core (@a2ui/web_core)
// and report whether it accepted every message. This is the conformance check:
// our Python validator and our small browser renderer must agree with it.
//
//   node conformance.mjs messages.jsonl      -> prints {"ok":..., "errors":[...], "surfaces":{id: dataModel}}
import { readFileSync } from "node:fs";
import { z } from "zod";
import { MessageProcessor, basicCatalog, Catalog, spec } from "@a2ui/web_core/v1_0";

const HTML_CATALOG_ID = "https://catalogs.genux.example/html/v1/catalog.json";

// Our custom catalog, declared the way web_core declares the basic one.
const HtmlFrameApi = {
  name: "HtmlFrame",
  schema: spec(z.object({
    title: z.any().optional(),
    html: z.string(),
    caption: z.any().optional(),
    allowedEvents: z.array(z.string()).optional(),
  }).strict(), { mixins: [] }),
};
const htmlCatalog = new Catalog(HTML_CATALOG_ID, "1.0", [HtmlFrameApi]);

const errors = [];
const processor = new MessageProcessor([basicCatalog, htmlCatalog], undefined, {
  version: "1.0", reportErrorsOnly: true, errorHandler: (e) => errors.push(e.error ?? e),
});

const text = readFileSync(process.argv[2] ?? 0, "utf8");
const messages = text.split("\n").map((l) => l.trim()).filter(Boolean).map((l) => JSON.parse(l));
processor.processMessages(messages);

const surfaces = {};
for (const m of messages) {
  const id = m.createSurface?.surfaceId;
  if (id && processor.model.getSurface(id)) surfaces[id] = processor.model.getSurface(id).dataModel.get("/");
}
console.log(JSON.stringify({ ok: errors.length === 0, messages: messages.length, errors, surfaces }));
