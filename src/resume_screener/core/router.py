"""Model provider abstraction.

Every tier calls `complete()` on a Model instance and never touches a
provider SDK directly. Swapping Anthropic for Microsoft Foundry is a
base_url and auth change, not an architecture change -- that claim only
holds if nothing in core/ ever imports `anthropic` directly, so don't.

`complete()` returns a ModelResponse, not a bare string, specifically so
real token accounting survives the abstraction. The cost methodology in
research/cost_latency_methodology.md depends on summing actual
cache_read/cache_creation token counts per call; an interface that
returned only text would make that impossible to measure honestly.
"""

from __future__ import annotations

import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field


@dataclass
class Usage:
    """Real token accounting for one call. Zeros for providers that don't report."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    latency_s: float = 0.0
    model_id: str = ""

    def __add__(self, other: Usage) -> Usage:
        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_input_tokens=self.cache_creation_input_tokens
            + other.cache_creation_input_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens
            + other.cache_read_input_tokens,
            latency_s=self.latency_s + other.latency_s,
            model_id=self.model_id or other.model_id,
        )


@dataclass
class ModelResponse:
    text: str
    usage: Usage = field(default_factory=Usage)


class Model(ABC):
    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
        temperature: float = 0.0,
    ) -> ModelResponse:
        """Run one completion.

        `system` is the cacheable prefix -- callers must put ONLY content
        that is byte-identical across many calls here (rubric + job
        description), and push anything that varies per call (persona,
        candidate evidence) into `user`. Caching is prefix-based, so a
        system string that differs per call silently defeats it.

        Default temperature is 0, not the provider's default -- this is a
        scoring task, not creative generation.
        """


class AnthropicModel(Model):
    """Default provider. Also the exact code path that runs unmodified
    against Anthropic's Claude models hosted in Microsoft Foundry -- only
    the base_url and auth differ.
    """

    def __init__(self, model_id: str, api_key: str, base_url: str | None = None):
        from anthropic import AsyncAnthropic

        self._model_id = model_id
        self._client = AsyncAnthropic(api_key=api_key, base_url=base_url)

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
        temperature: float = 0.0,
    ) -> ModelResponse:
        system_block = [
            {
                "type": "text",
                "text": system,
                **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
            }
        ]
        started = time.monotonic()
        response = await self._client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_block,
            messages=[{"role": "user", "content": user}],
        )
        elapsed = time.monotonic() - started
        raw = response.usage
        return ModelResponse(
            text=response.content[0].text,
            usage=Usage(
                input_tokens=raw.input_tokens,
                output_tokens=raw.output_tokens,
                cache_creation_input_tokens=getattr(raw, "cache_creation_input_tokens", 0) or 0,
                cache_read_input_tokens=getattr(raw, "cache_read_input_tokens", 0) or 0,
                latency_s=elapsed,
                model_id=self._model_id,
            ),
        )


class OllamaModel(Model):
    """Local provider. Implemented and tested against a mocked endpoint;
    deliberately not wired into the default cascade -- see README for why
    (VRAM/compute limits, not a code limitation).
    """

    def __init__(self, model_id: str, host: str = "http://localhost:11434"):
        self._model_id = model_id
        self._host = host

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
        temperature: float = 0.0,
    ) -> ModelResponse:
        import httpx

        started = time.monotonic()
        async with httpx.AsyncClient(base_url=self._host, timeout=120.0) as client:
            resp = await client.post(
                "/api/chat",
                json={
                    "model": self._model_id,
                    "messages": [
                        {"role": "system", "content": system},
                        {"role": "user", "content": user},
                    ],
                    "options": {"temperature": temperature},
                    "stream": False,
                },
            )
            resp.raise_for_status()
            body = resp.json()
        return ModelResponse(
            text=body["message"]["content"],
            usage=Usage(
                input_tokens=body.get("prompt_eval_count", 0) or 0,
                output_tokens=body.get("eval_count", 0) or 0,
                latency_s=time.monotonic() - started,
                model_id=self._model_id,
            ),
        )
