"""A minimal coding-agent harness: the loop, workspace tools, and UI tools.

The loop is the one every coding harness (Claude Code, Codex, the course's
simple-coding-harness) is built on:

    messages = [system, user]
    repeat:
        reply = model(messages, tools)
        if reply has no tool calls: done
        for each tool call: run the tool, append the result as a "tool" message

Generative UI joins the harness as **tools**. A UI tool does not compute
anything; it hands a description of an interface to the *surfaces* that are
listening (a terminal, a web page over AG-UI). Its result goes back to the
model like any other tool result - including validation errors, which lets
the model correct its own UI.

Every step emits an event; surfaces subscribe to them:
    run_started, text, tool_call, tool_result, ui, run_finished
"""

from __future__ import annotations

import json
import shutil
import tempfile
import uuid
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable

SHARED = Path(__file__).resolve().parent
TEMPLATE = SHARED / "workspace_template"


@dataclass
class Tool:
    name: str
    description: str
    parameters: dict
    fn: Callable[..., str | dict]
    ui: bool = False                      # UI tools are rendered by surfaces

    def schema(self) -> dict:
        return {"name": self.name, "description": self.description, "parameters": self.parameters}


@dataclass
class Harness:
    llm: object
    system: str
    tools: list[Tool]
    fixture: str
    max_turns: int = 8
    listeners: list[Callable[[str, dict], None]] = field(default_factory=list)
    messages: list[dict] = field(default_factory=list)

    def on(self, listener):
        self.listeners.append(listener)
        return self

    def emit(self, kind: str, **data):
        for listener in self.listeners:
            listener(kind, data)

    def run(self, user_text: str) -> str:
        """One user turn. The conversation (self.messages) persists across turns."""
        if not self.messages:
            self.messages.append({"role": "system", "content": self.system})
        self.messages.append({"role": "user", "content": user_text})
        self.emit("run_started", user=user_text)
        by_name = {t.name: t for t in self.tools}
        final = ""
        for _ in range(self.max_turns):
            reply = self.llm.chat(messages=self.messages, tools=[t.schema() for t in self.tools], fixture=self.fixture)
            calls = reply["tool_calls"]
            self.messages.append({"role": "assistant", "content": reply["content"], "tool_calls": [
                {"id": c["id"], "type": "function", "function": {"name": c["name"], "arguments": json.dumps(c["arguments"])}} for c in calls]})
            if reply["content"]:
                self.emit("text", text=reply["content"])
                final = reply["content"]
            if not calls:
                break
            for call in calls:
                self.emit("tool_call", id=call["id"], name=call["name"], arguments=call["arguments"])
                tool = by_name.get(call["name"])
                try:
                    out = tool.fn(**call["arguments"]) if tool else {"error": f"unknown tool {call['name']}"}
                except Exception as exc:  # a failing tool is a result, not a crash
                    out = {"error": f"{type(exc).__name__}: {exc}"}
                ok = not (isinstance(out, dict) and "error" in out)
                if tool and tool.ui and ok:
                    self.emit("ui", tool=call["name"], arguments=call["arguments"], result=out)
                self.emit("tool_result", id=call["id"], name=call["name"], result=out, ok=ok)
                self.messages.append({"role": "tool", "tool_call_id": call["id"],
                                      "content": out if isinstance(out, str) else json.dumps(out)})
        self.emit("run_finished", text=final)
        return final


# ------------------------------------------------------------------ workspace tools
class Workspace:
    """A private copy of the data folder; the agent can read and write only inside it."""

    def __init__(self):
        self.root = Path(tempfile.mkdtemp(prefix="genux-ws-"))
        shutil.copytree(TEMPLATE, self.root, dirs_exist_ok=True)

    def path(self, rel: str) -> Path:
        p = (self.root / rel).resolve()
        if not str(p).startswith(str(self.root.resolve())):
            raise PermissionError(f"{rel} is outside the workspace")
        return p

    def tools(self) -> list[Tool]:
        return [
            Tool("list_files", "List the files in the workspace.", {"type": "object", "properties": {}},
                 lambda: "\n".join(sorted(p.name for p in self.root.iterdir()))),
            Tool("read_file", "Read a text file from the workspace.",
                 {"type": "object", "properties": {"path": {"type": "string"}}, "required": ["path"]},
                 lambda path: self.path(path).read_text(encoding="utf-8")),
        ]


def new_id(prefix: str) -> str:
    return f"{prefix}_{uuid.uuid4().hex[:8]}"
