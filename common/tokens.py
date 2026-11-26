"""Token counting for the cost comparisons, always with the o200k_base tokenizer when possible.

Order of preference:
1. Node ``gpt-tokenizer`` (``npm install`` in the repo root; the encoding ships inside the package,
   so it works offline);
2. Python ``tiktoken`` (downloads its data file on first use);
3. a rough estimate (characters / 4), clearly labelled as such.
"""

from __future__ import annotations

import json
import shutil
import subprocess
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parents[1]
NODE_SCRIPT = ROOT / "common" / "node" / "count_tokens.mjs"


@lru_cache(maxsize=None)
def _backend() -> str:
    if shutil.which("node") and (ROOT / "node_modules" / "gpt-tokenizer").exists():
        return "node"
    try:
        import tiktoken

        tiktoken.get_encoding("o200k_base")
        return "tiktoken"
    except Exception:
        return "estimate"


@lru_cache(maxsize=4096)
def count(text: str) -> int:
    backend = _backend()
    if backend == "tiktoken":
        import tiktoken

        return len(tiktoken.get_encoding("o200k_base").encode(text))
    if backend == "node":
        out = subprocess.run(["node", str(NODE_SCRIPT)], input=json.dumps([text]), capture_output=True, text=True, timeout=60)
        return json.loads(out.stdout)[0]
    return max(1, len(text) // 4)


def method() -> str:
    return {"tiktoken": "o200k_base via tiktoken", "node": "o200k_base via gpt-tokenizer",
            "estimate": "estimate: characters / 4"}[_backend()]
