"""Model provider abstraction.

Every tier calls `complete()` on a Model instance and never touches a
provider SDK directly. Swapping Anthropic for Microsoft Foundry is a
base_url and auth change, not an architecture change -- that claim only
holds if nothing in core/ ever imports `anthropic` directly, so don't.
"""

from __future__ import annotations

from abc import ABC, abstractmethod
from dataclasses import dataclass


@dataclass
class ModelTier:
    """One rung of the cascade. Not tied to a specific vendor's model name."""

    name: str  # "triage" | "panel" | "arbiter"
    model_id: str


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
    ) -> str:
        """Return the model's raw text response.

        Default temperature is 0, not the provider's default -- this is a
        scoring task, not creative generation. See
        research/stonestepper_ablation_review.md; StoneStepper's own
        ablation baseline is temp 0 for the same reason, and this code
        previously left it unset, silently riding whatever the API
        defaults to.
        """


class AnthropicModel(Model):
    """Default provider. Also the exact code path that runs unmodified
    against Anthropic's Claude models hosted in Microsoft Foundry -- only
    the base_url and auth differ, per Anthropic's own Foundry integration.
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
    ) -> str:
        system_block = [
            {
                "type": "text",
                "text": system,
                **({"cache_control": {"type": "ephemeral"}} if cache_system else {}),
            }
        ]
        response = await self._client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            temperature=temperature,
            system=system_block,
            messages=[{"role": "user", "content": user}],
        )
        return response.content[0].text


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
    ) -> str:
        import httpx

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
            return resp.json()["message"]["content"]
