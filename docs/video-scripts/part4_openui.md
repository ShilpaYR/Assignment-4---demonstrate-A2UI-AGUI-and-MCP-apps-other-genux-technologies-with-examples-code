# Video 4 - OpenUI Lang: a compact, streaming UI language (≈12 min)

**Goal:** show the language (positional args, forward references), the official parser in Node and in the browser, the token comparison, and edits.

Before recording: `npm install && npm run build` (bundles the official parser into `shared/web/vendor/`).

| Time | On screen | Do | Say |
|---|---|---|---|
| 0:00 | `04_openui/README.md` | Program example | "OpenUI Lang from thesys: one statement per line, positional arguments, names usable before they're defined. The library decides which components exist." |
| 0:45 | `shared/library.mjs`, `shared/build.mjs`, `generated/prompt_declarative.txt` | — | "Four libraries: static, declarative, html, hybrid. The prompt and the parser schema come from the library; the parser is bundled for the browser." |
| 1:30 | lab1_static (8041) | Run; Reorder 10 kg | "Static: the library holds two pre-built components; the whole answer is three lines." Wire: chunks, then the edit statement. |
| 2:15 | `server.py`, `page/app.js` `PREBUILT`, `oui-render.js` `set()` | Steps 1-6 | "The page owns the look; the model fills positional arguments. An action returns a statement; mergeStatements applies it." |
| 3:45 | lab2_declarative (8042) | Run with the status line visible | "Declarative: primitives. Watch 'pending': forward references resolve as their lines arrive." |
| 4:30 | `page/app.js`, `oui-render.js` pending chip | Steps 1-4 | — |
| 5:30 | Terminal | `python demo.py` | Read "after N lines ... unresolved" and the token table (OpenUI vs JSON formats). "These are this sample's numbers with o200k_base." |
| 6:30 | lab3_open_ended (8043) | Run; the "still writing" placeholder, then use the calculator | "Open-ended: HtmlArtifact. The document is a string literal; the parser marks it partial until the string closes - half a document never runs." |
| 7:15 | `library.mjs` HtmlArtifact, `oui-render.js` `artifact()`, `server.py` policy | Steps 1-4 | "The policy runs on the parsed document, not on the program text." |
| 8:30 | lab4_mixed (8044) | Calculator → "Use this price"; Reorder | "Mixed: primitives plus one artifact. Both user events come back as one-line edits." |
| 9:15 | `server.py` `handle_action`, `oui-render.js` `edit()`, `page/app.js` share | Steps 1-4 | "Only the changed statement re-renders; the artifact is never re-mounted. And it's 70% of the token budget." |
| 11:00 | Terminal | `python demo.py`, pytest | "after both edits the artifact still shows price $4.20". |
| 11:40 | Part README | — | "Next: MCP Apps - your UI inside somebody else's host." |
