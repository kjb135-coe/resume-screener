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
    truncated: bool = False
    """The model hit max_tokens mid-answer.

    Worth distinguishing from a genuine parse failure: truncated JSON is a
    budget problem we control, not the model misbehaving. Extended thinking
    spends the same max_tokens budget as the visible answer, so a limit that
    looks generous for the output alone can still cut the answer in half.
    """


def _first_text_block(content: list) -> str:
    """Pull the assistant's text out of a response's content blocks.

    A response is a LIST of blocks, and text is not guaranteed to be first:
    models that use extended thinking put a ThinkingBlock at index 0, so
    `content[0].text` raises AttributeError. That failure is intermittent --
    it depends on whether the model thought on that particular call -- which
    makes it especially worth handling explicitly rather than indexing and
    hoping.
    """
    for block in content:
        if getattr(block, "type", None) == "text":
            return block.text
    # No text block at all (e.g. the model only emitted thinking, or hit a
    # stop reason mid-block). Callers treat an empty string as a parse
    # failure and fall back, which is the right behaviour here.
    return ""


class Model(ABC):
    @abstractmethod
    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
    ) -> ModelResponse:
        """Run one completion.

        `system` is the cacheable prefix -- callers must put ONLY content
        that is byte-identical across many calls here (rubric + job
        description), and push anything that varies per call (persona,
        candidate evidence) into `user`. Caching is prefix-based, so a
        system string that differs per call silently defeats it.

        There is deliberately no `temperature` argument. The Anthropic SDK
        removed it in 1.0 (sampling is no longer a caller-facing knob), and
        an interface advertising a parameter its primary provider ignores
        would be worse than not having one. Providers that do expose
        sampling controls take them as constructor arguments instead --
        see OllamaModel.
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
            system=system_block,
            messages=[{"role": "user", "content": user}],
        )
        elapsed = time.monotonic() - started
        raw = response.usage
        return ModelResponse(
            truncated=getattr(response, "stop_reason", None) == "max_tokens",
            text=_first_text_block(response.content),
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

    def __init__(
        self,
        model_id: str,
        host: str = "http://localhost:11434",
        temperature: float = 0.0,
    ):
        self._model_id = model_id
        self._host = host
        # Scoring is a classification task, not creative generation, so this
        # defaults to deterministic. Provider-specific because Anthropic no
        # longer exposes sampling controls at all.
        self._temperature = temperature

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
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
                    "options": {"temperature": self._temperature},
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
