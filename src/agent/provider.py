"""Model provider with a disk cache keyed by prompt and sampling settings.

The agent, the signal extractors, and the grader all talk to a language model
through this module. Every call is cached under data/cache/ keyed by the full
request (model, messages, seed, temperature, token limits, logprob flags), so
a rerun with the same inputs never touches the model again and results are
reproducible.

OllamaProvider uses Ollama's native /api/chat endpoint because it exposes the
seed, the context length, and per-token log probabilities in one place. A
reply is parsed before it is cached, so a malformed reply is never stored, and
a cache file that cannot be read (for example one truncated by a crash) counts
as a miss and is rewritten.
"""

from __future__ import annotations

import hashlib
import json
import os
from dataclasses import dataclass, field
from pathlib import Path
from typing import Callable, Optional, Protocol

Transport = Callable[[str, dict], dict]


class Provider(Protocol):
    """What the agent, the signals and the grader need from a model backend.

    OllamaProvider is the only implementation. A hosted OpenAI-compatible
    backend would be a second class with the same two members; the owner
    decided not to build it until it is needed.
    """

    model: str

    def generate(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        seed: int = 42,
        max_tokens: int = 512,
        logprobs: bool = False,
        top_logprobs: int = 0,
    ) -> "Generation": ...


@dataclass
class Generation:
    """One model reply. Token fields are None when logprobs were not requested."""

    text: str
    model: str
    cached: bool
    tokens: Optional[list[str]] = None
    logprobs: Optional[list[float]] = None
    top_logprobs: Optional[list[list[tuple[str, float]]]] = None
    raw: dict = field(default_factory=dict, repr=False)


def _http_transport(url: str, body: dict) -> dict:
    import httpx

    response = httpx.post(url, json=body, timeout=600.0)
    response.raise_for_status()
    return response.json()


class OllamaProvider:
    """Talks to Ollama's native chat endpoint and caches every reply on disk."""

    name = "ollama"

    def __init__(
        self,
        model: str,
        base_url: str = "http://localhost:11434",
        cache_dir: str | Path = "data/cache",
        transport: Optional[Transport] = None,
        num_ctx: int = 4096,
    ):
        self.model = model
        self.base_url = base_url.rstrip("/")
        self.cache_dir = Path(cache_dir)
        self.transport = transport or _http_transport
        self.num_ctx = num_ctx

    def generate(
        self,
        messages: list[dict],
        *,
        temperature: float = 0.0,
        seed: int = 42,
        max_tokens: int = 512,
        logprobs: bool = False,
        top_logprobs: int = 0,
    ) -> Generation:
        body = {
            "model": self.model,
            "messages": messages,
            "stream": False,
            "logprobs": logprobs,
            "top_logprobs": top_logprobs,
            "options": {
                "seed": seed,
                "temperature": temperature,
                "num_predict": max_tokens,
                "num_ctx": self.num_ctx,
            },
        }
        path = self._cache_path(body)
        stored = self._read_cache(path)
        if stored is not None:
            return self._parse(stored["response"], cached=True)

        raw = self.transport(f"{self.base_url}/api/chat", body)
        generation = self._parse(raw, cached=False)
        self._write_cache(path, body, raw)
        return generation

    def _cache_path(self, body: dict) -> Path:
        payload = json.dumps({"provider": self.name, "body": body}, sort_keys=True, ensure_ascii=False)
        key = hashlib.sha256(payload.encode("utf-8")).hexdigest()
        return self.cache_dir / key[:2] / f"{key}.json"

    @staticmethod
    def _read_cache(path: Path) -> Optional[dict]:
        """The stored call, or None when the file is missing, truncated, or unreadable."""
        if not path.exists():
            return None
        try:
            stored = json.loads(path.read_text(encoding="utf-8"))
        except (OSError, ValueError):
            return None
        return stored if isinstance(stored, dict) and "response" in stored else None

    @staticmethod
    def _write_cache(path: Path, body: dict, raw: dict) -> None:
        path.parent.mkdir(parents=True, exist_ok=True)
        partial = path.with_name(path.name + ".tmp")
        partial.write_text(
            json.dumps({"request": body, "response": raw}, ensure_ascii=False),
            encoding="utf-8",
            newline="\n",
        )
        os.replace(partial, path)

    def _parse(self, raw: dict, cached: bool) -> Generation:
        try:
            text = raw["message"]["content"]
        except (KeyError, TypeError):
            raise ValueError(f"reply from {self.name} has no message content: {json.dumps(raw)[:200]}") from None
        entries = raw.get("logprobs") or None
        tokens = logprobs = top = None
        if entries:
            tokens = [e["token"] for e in entries]
            logprobs = [float(e["logprob"]) for e in entries]
            top = [[(a["token"], float(a["logprob"])) for a in e.get("top_logprobs", [])] for e in entries]
        return Generation(
            text=text,
            model=raw.get("model", self.model),
            cached=cached,
            tokens=tokens,
            logprobs=logprobs,
            top_logprobs=top,
            raw=raw,
        )
