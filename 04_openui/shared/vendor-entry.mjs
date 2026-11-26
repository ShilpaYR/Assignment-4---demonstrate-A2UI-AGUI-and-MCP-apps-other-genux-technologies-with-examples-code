// Entry for the browser bundle of the OFFICIAL OpenUI Lang parser.
// `npm run build:openui` bundles it with esbuild into web/vendor/openui-lang-core.js.
export { createParser, createStreamingParser, mergeStatements } from "@openuidev/lang-core";
