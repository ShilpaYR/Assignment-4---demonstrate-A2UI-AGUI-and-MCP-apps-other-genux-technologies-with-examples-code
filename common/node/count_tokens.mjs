// Count o200k_base tokens (the GPT-4o / GPT-4.1 tokenizer) with gpt-tokenizer, which ships the
// encoding inside the npm package - used when Python's tiktoken cannot download its data file.
//   node count_tokens.mjs < texts.json      (a JSON array of strings)  -> JSON array of counts
import { readFileSync } from "node:fs";
import { encode } from "gpt-tokenizer/encoding/o200k_base";
const texts = JSON.parse(readFileSync(0, "utf8"));
console.log(JSON.stringify(texts.map((t) => encode(t).length)));
