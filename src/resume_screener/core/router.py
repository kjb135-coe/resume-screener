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

import asyncio
import random
import re
import time
from abc import ABC, abstractmethod
from dataclasses import dataclass, field

_TOKEN_FIELDS = (
    "input_tokens",
    "output_tokens",
    "cache_creation_input_tokens",
    "cache_read_input_tokens",
)


@dataclass
class Usage:
    """Real token accounting for one call. Zeros for providers that don't report."""

    input_tokens: int = 0
    output_tokens: int = 0
    cache_creation_input_tokens: int = 0
    cache_read_input_tokens: int = 0
    latency_s: float = 0.0
    model_id: str = ""

    by_model: dict[str, dict[str, int]] = field(default_factory=dict)
    """Tokens split by the model that actually spent them.

    The scalar fields above collapse a cascade into one number, and
    `model_id` keeps only the first model seen. That was silently wrong for
    cost: a Verdict accumulates Haiku extraction, Sonnet panel calls and an
    Opus arbiter call, ends up labelled `haiku`, and gets priced entirely at
    Haiku rates -- understating a real run several-fold, because Opus output
    costs 15x Haiku output.

    Splitting here rather than at the reporting layer means the split
    survives every `+` in the pipeline, which is the only place that knows
    which model ran.
    """

    def __post_init__(self) -> None:
        if not self.by_model and self.model_id and any(
            getattr(self, f) for f in _TOKEN_FIELDS
        ):
            self.by_model = {self.model_id: {f: getattr(self, f) for f in _TOKEN_FIELDS}}

    def __add__(self, other: Usage) -> Usage:
        merged: dict[str, dict[str, int]] = {}
        for source in (self.by_model, other.by_model):
            for model, counts in source.items():
                target = merged.setdefault(model, dict.fromkeys(_TOKEN_FIELDS, 0))
                for field_name, value in counts.items():
                    target[field_name] = target.get(field_name, 0) + value

        return Usage(
            input_tokens=self.input_tokens + other.input_tokens,
            output_tokens=self.output_tokens + other.output_tokens,
            cache_creation_input_tokens=self.cache_creation_input_tokens
            + other.cache_creation_input_tokens,
            cache_read_input_tokens=self.cache_read_input_tokens
            + other.cache_read_input_tokens,
            latency_s=self.latency_s + other.latency_s,
            model_id=self.model_id or other.model_id,
            by_model=merged,
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

    def __init__(
        self,
        model_id: str,
        api_key: str,
        base_url: str | None = None,
        prefill: str = "",
    ):
        from anthropic import AsyncAnthropic

        self._model_id = model_id
        self._prefill = prefill
        """Text to put in the assistant's mouth before it answers.

        Set it to `{` and the model cannot open with "Here is the JSON:"
        -- it is already mid-object. Every tier in this pipeline asks for
        JSON in prose and nothing enforces it, which is what rejected an
        all-Haiku panel in PLAN.md section 8a: 49% of its responses were
        unparseable, against 2.2% for Sonnet on the identical prompt.
        That was read at the time as a structured-output problem rather
        than a capability problem, and this is the knob that tests it.

        Off by default. Turning it on changes what the model emits, so
        the production config does not get it silently -- it is opt-in
        per arm in config/bakeoff.json until an eval says it helps.
        """
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
        messages: list[dict] = [{"role": "user", "content": user}]
        if self._prefill:
            messages.append({"role": "assistant", "content": self._prefill})
        started = time.monotonic()
        response = await self._client.messages.create(
            model=self._model_id,
            max_tokens=max_tokens,
            system=system_block,
            messages=messages,
        )
        elapsed = time.monotonic() - started
        raw = response.usage
        return ModelResponse(
            truncated=getattr(response, "stop_reason", None) == "max_tokens",
            # The prefill is not echoed back, so callers would receive
            # JSON missing its opening brace. Stitching it back here keeps
            # prefill invisible to every caller and parser.
            text=self._prefill + _first_text_block(response.content),
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


_RETRY_IN_RE = re.compile(r"retry in ([0-9]+(?:\.[0-9]+)?)s", re.IGNORECASE)


def _retry_delay_from(resp) -> str | None:
    """The delay the provider asked for, as a string of seconds, or None.

    Two places to look, because providers disagree. OpenAI sends a
    `Retry-After` header. Google sends no header at all and buries
    "Please retry in 4.613214581s" in the JSON error message, so a
    header-only reader silently falls back to its own guess against the
    one provider most likely to throttle.
    """
    header = resp.headers.get("Retry-After")
    if header:
        return header
    try:
        body = resp.json()
    except Exception:  # noqa: BLE001 - a non-JSON error body is not exceptional
        return None
    if isinstance(body, list):
        body = body[0] if body else {}
    if not isinstance(body, dict):
        return None
    message = (body.get("error") or {})
    message = message.get("message") if isinstance(message, dict) else None
    if not isinstance(message, str):
        return None
    found = _RETRY_IN_RE.search(message)
    return found.group(1) if found else None


class OpenAICompatibleModel(Model):
    """Any provider that speaks the OpenAI `/chat/completions` shape.

    One adapter rather than three SDKs, because OpenAI, Google (Gemini's
    OpenAI-compatibility endpoint) and Zhipu (GLM) all expose this format.
    Adding a provider is then a base_url and a model id in
    `config/bakeoff.json`, not new code -- which matters for a bake-off
    whose whole point is swapping providers cheaply.

    Everything provider-specific is passthrough rather than hardcoded,
    because the exact spelling of these knobs differs per provider and
    changes between model generations:

    - `token_param` -- newer reasoning models renamed `max_tokens` to
      `max_completion_tokens` and reject the old name outright.
    - `send_temperature` -- several reasoning models reject `temperature`
      at any value, including the 0.0 this pipeline would want.
    - `extra_body` -- anything else the provider wants merged into the
      request, e.g. `{"reasoning_effort": "medium"}`.

    Guessing any of these wrong fails at request time and reads like a
    model problem rather than a config problem, so none of them are
    guessed here.
    """

    def __init__(
        self,
        model_id: str,
        api_key: str,
        base_url: str,
        *,
        temperature: float = 0.0,
        send_temperature: bool = True,
        token_param: str = "max_tokens",
        extra_body: dict | None = None,
        timeout_s: float = 180.0,
        max_retries: int = 5,
        backoff_base: float = 2.0,
        backoff_max: float = 60.0,
    ):
        self._model_id = model_id
        self._api_key = api_key
        self._base_url = base_url.rstrip("/")
        self._temperature = temperature
        self._send_temperature = send_temperature
        self._token_param = token_param
        self._extra_body = dict(extra_body or {})
        self._timeout_s = timeout_s
        self._max_retries = max_retries
        self._backoff_base = backoff_base
        self._backoff_max = backoff_max

    async def _post_with_retry(self, client, payload: dict):
        """POST, retrying rate limits and transient server errors.

        The Anthropic SDK retries these internally, so nothing in this repo
        needed it until now. Raw httpx does not, and the gap is not
        academic: the first live Gemini run lost all 20 resumes to 429s,
        because 5 concurrent resumes x 3 panel agents is 15 requests in
        flight and the pipeline surfaced the first refusal as a hard
        failure.

        The provider's own delay is honoured when it gives one -- guessing
        a shorter delay against a provider that just told you the real one
        is how a rate limit turns into a ban. Google sends no `Retry-After`
        header and puts "Please retry in 4.6s" in the error body instead,
        so both are read. Otherwise back off exponentially with jitter, so
        parallel callers throttled together do not all wake together and
        throttle again.

        A per-DAY quota is not retryable and this will not rescue it: the
        free Gemini tier allows 20 requests per day per model, against the
        60+ one 20-resume run needs. That case is caught in
        scripts/bakeoff.py, which reports it rather than burning retries.
        """
        import httpx

        last: Exception | None = None
        for attempt in range(self._max_retries + 1):
            try:
                resp = await client.post(
                    f"{self._base_url}/chat/completions",
                    headers={
                        "Authorization": f"Bearer {self._api_key}",
                        "Content-Type": "application/json",
                    },
                    json=payload,
                )
            except httpx.TransportError as exc:
                # Connection reset / DNS / timeout. A biased subset of
                # dropped candidates is worse than a slow run: see the
                # discarded var3 in docs/RESULTS_HISTORY.md, where network
                # failures removed exactly the hard candidates.
                last = exc
                if attempt == self._max_retries:
                    raise
                await self._sleep_before_retry(attempt, None)
                continue

            if resp.status_code == 429 or resp.status_code >= 500:
                if attempt == self._max_retries:
                    return resp  # let raise_for_status() report it
                await self._sleep_before_retry(attempt, _retry_delay_from(resp))
                continue
            return resp
        raise last if last else RuntimeError("unreachable")

    async def _sleep_before_retry(self, attempt: int, retry_after: str | None) -> None:
        if retry_after:
            try:
                delay = float(retry_after)
            except ValueError:
                delay = self._backoff_base * (2**attempt)
        else:
            delay = self._backoff_base * (2**attempt)
        # Full jitter. Without it, every throttled request retries in
        # lockstep and re-triggers the same limit.
        await asyncio.sleep(min(delay, self._backoff_max) * (0.5 + random.random() / 2))

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
    ) -> ModelResponse:
        # `cache_system` is accepted and ignored. Anthropic takes an explicit
        # cache_control breakpoint; these providers either cache the prompt
        # prefix automatically or not at all. Reported cached tokens still
        # land in cache_read_input_tokens below, so cost accounting stays
        # honest -- but a cross-provider cost comparison is not like-for-like
        # on caching, and docs/BAKEOFF.md says so.
        import httpx

        payload = {
            "model": self._model_id,
            "messages": [
                {"role": "system", "content": system},
                {"role": "user", "content": user},
            ],
            self._token_param: max_tokens,
            **self._extra_body,
        }
        if self._send_temperature:
            payload["temperature"] = self._temperature

        started = time.monotonic()
        async with httpx.AsyncClient(timeout=self._timeout_s) as client:
            resp = await self._post_with_retry(client, payload)
            resp.raise_for_status()
            body = resp.json()

        choice = (body.get("choices") or [{}])[0]
        message = choice.get("message") or {}
        text = message.get("content") or ""
        # Some reasoning models return the answer as a list of parts rather
        # than a string. Join rather than crash.
        if isinstance(text, list):
            text = "".join(
                part.get("text", "") for part in text if isinstance(part, dict)
            )

        usage = body.get("usage") or {}
        # Nested and differently named per provider; absent is not an error.
        cached = 0
        details = usage.get("prompt_tokens_details")
        if isinstance(details, dict):
            cached = details.get("cached_tokens", 0) or 0

        return ModelResponse(
            text=text or "",
            usage=Usage(
                # Providers report the cached portion inside prompt_tokens.
                # Subtract it so input_tokens means "billed at full rate",
                # matching what AnthropicModel reports.
                input_tokens=max((usage.get("prompt_tokens", 0) or 0) - cached, 0),
                output_tokens=usage.get("completion_tokens", 0) or 0,
                cache_read_input_tokens=cached,
                latency_s=time.monotonic() - started,
                model_id=self._model_id,
            ),
            truncated=choice.get("finish_reason") == "length",
        )
