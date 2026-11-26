// A minimal AG-UI client: POST a RunAgentInput, read the SSE stream of events.
// The official @ag-ui/client HttpAgent does the same plus retries, typing and
// message bookkeeping; writing it by hand shows there is no magic in the wire.
import { postSSE } from "./sse.js";

let counter = 0;
export const newId = (prefix) => `${prefix}_${Date.now().toString(36)}_${(counter++).toString(36)}`;

export function runAgent(url, { threadId, messages = [], state = {}, tools = [], forwardedProps = {} }, onEvent) {
  const input = { threadId, runId: newId("run"), messages, state, tools, context: [], forwardedProps };
  return postSSE(url, input, (event) => onEvent(event)).then(() => input);
}
