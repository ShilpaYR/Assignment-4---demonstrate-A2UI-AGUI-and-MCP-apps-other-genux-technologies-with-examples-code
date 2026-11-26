"""One small model client for every lab.

Two implementations with the same three methods:

* ``ScriptedLLM`` (default) replays a reply stored in the lab's ``fixtures/``
  folder. Tests and demos use it, so the whole repository runs offline,
  for free, and gives the same output every time.
* ``LiveLLM`` calls any OpenAI-compatible endpoint. Turn it on with
  ``GENUX_LIVE=1`` plus ``API_KEY`` (or ``OPENAI_API_KEY``); optional
  ``BASE_URL`` and ``MODEL`` (default ``gpt-4.1-mini``).

The lab code never knows which one it talks to: the system prompt, the
validation and the rendering are identical in both modes. Only the source
of the text changes.

Methods
-------
text(system, user, fixture)            -> str            (one complete reply)
stream(system, user, fixture)          -> Iterator[str]  (the same reply in chunks)
chat(messages, tools, fixture)         -> {"content", "tool_calls"}  (function calling)
"""

from __future__ import annotations

import json
import os
import time
import uuid
from pathlib import Path
from typing import Iterator


def _env(name: str, default: str | None = None) -> str | None:
    value = os.environ.get(name)
    return value if value else default


def stream_delay() -> float:
    """Seconds between streamed chunks. Demos use a small delay so streaming is visible."""
    return float(_env("GENUX_STREAM_DELAY", "0") or 0)


class ScriptedLLM:
    """Replays ``fixtures/<name>.txt`` (text) or ``fixtures/<name>.json`` (chat turns)."""

    mode = "scripted"

    def __init__(self, fixtures_dir: str | Path, chunk_size: int = 28):
        self.fixtures_dir = Path(fixtures_dir)
        self.chunk_size = chunk_size
        self.calls: list[dict] = []  # what the lab sent, so tests can inspect the prompt

    def _read(self, fixture: str) -> str:
        for ext in (".txt", ".jsonl", ".html", ".oui", ".json"):
            path = self.fixtures_dir / f"{fixture}{ext}"
            if path.exists():
                return path.read_text(encoding="utf-8")
        raise FileNotFoundError(f"no fixture named {fixture!r} in {self.fixtures_dir}")

    def text(self, *, system: str, user: str, fixture: str) -> str:
        self.calls.append({"system": system, "user": user, "fixture": fixture})
        return self._read(fixture)

    def stream(self, *, system: str, user: str, fixture: str) -> Iterator[str]:
        reply = self.text(system=system, user=user, fixture=fixture)
        delay = stream_delay()
        for i in range(0, len(reply), self.chunk_size):
            if delay:
                time.sleep(delay)
            yield reply[i : i + self.chunk_size]

    def chat(self, *, messages: list[dict], tools: list[dict], fixture: str) -> dict:
        """Return assistant turn number N, where N = assistant messages already sent."""
        self.calls.append({"messages": messages, "tools": tools, "fixture": fixture})
        turns = json.loads(self._read(fixture))
        index = sum(1 for m in messages if m.get("role") == "assistant")
        turn = turns[min(index, len(turns) - 1)]
        calls = [
            {"id": c.get("id") or f"call_{uuid.uuid4().hex[:8]}", "name": c["name"], "arguments": c.get("arguments", {})}
            for c in turn.get("tool_calls", [])
        ]
        return {"content": turn.get("content"), "tool_calls": calls}


class LiveLLM:
    """Any OpenAI-compatible chat-completions endpoint."""

    mode = "live"

    def __init__(self):
        from openai import OpenAI  # imported lazily: offline runs do not need the package

        self.model = _env("MODEL", "gpt-4.1-mini")
        self.client = OpenAI(
            api_key=_env("API_KEY") or _env("OPENAI_API_KEY"),
            base_url=_env("BASE_URL", "https://api.openai.com/v1"),
        )
        self.calls: list[dict] = []

    def text(self, *, system: str, user: str, fixture: str = "") -> str:
        return "".join(self.stream(system=system, user=user, fixture=fixture))

    def stream(self, *, system: str, user: str, fixture: str = "") -> Iterator[str]:
        self.calls.append({"system": system, "user": user})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=[{"role": "system", "content": system}, {"role": "user", "content": user}],
            stream=True,
        )
        for event in response:
            if event.choices and event.choices[0].delta.content:
                yield event.choices[0].delta.content

    def chat(self, *, messages: list[dict], tools: list[dict], fixture: str = "") -> dict:
        self.calls.append({"messages": messages, "tools": tools})
        response = self.client.chat.completions.create(
            model=self.model,
            messages=messages,
            tools=[{"type": "function", "function": t} for t in tools] or None,
        )
        msg = response.choices[0].message
        calls = []
        for c in msg.tool_calls or []:
            try:
                args = json.loads(c.function.arguments or "{}")
            except json.JSONDecodeError:
                args = {"_raw": c.function.arguments}
            calls.append({"id": c.id, "name": c.function.name, "arguments": args})
        return {"content": msg.content, "tool_calls": calls}


def get_llm(fixtures_dir: str | Path):
    """Scripted unless GENUX_LIVE=1 and a key is set."""
    if _env("GENUX_LIVE") == "1" and (_env("API_KEY") or _env("OPENAI_API_KEY")):
        return LiveLLM()
    return ScriptedLLM(fixtures_dir)


def strip_fences(text: str) -> str:
    """Models sometimes wrap output in ``` fences. Remove one outer fence if present."""
    t = text.strip()
    if t.startswith("```"):
        t = t.split("\n", 1)[1] if "\n" in t else ""
        if t.rstrip().endswith("```"):
            t = t.rstrip()[:-3]
    return t.strip()
