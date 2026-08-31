"""Response parsing in the provider layer.

The text-block extraction is regression-tested because getting it wrong is
silent and intermittent: it only fails when the model happens to emit a
thinking block, so it can pass a smoke test and then break most of a batch.
"""

from __future__ import annotations

import json
from dataclasses import dataclass
from typing import ClassVar

import pytest

from resume_screener.core.router import Usage, _first_text_block


@dataclass
class Block:
    type: str
    text: str = ""


class TestFirstTextBlock:
    def test_plain_text_response(self):
        assert _first_text_block([Block("text", "hello")]) == "hello"

    def test_skips_leading_thinking_block(self):
        content = [Block("thinking"), Block("text", '{"score": 8}')]
        assert _first_text_block(content) == '{"score": 8}'

    def test_skips_multiple_non_text_blocks(self):
        content = [Block("thinking"), Block("redacted_thinking"), Block("text", "answer")]
        assert _first_text_block(content) == "answer"

    def test_no_text_block_returns_empty_not_crash(self):
        assert _first_text_block([Block("thinking")]) == ""

    def test_empty_content_returns_empty(self):
        assert _first_text_block([]) == ""


class TestUsage:
    def test_addition_accumulates_every_field(self):
        a = Usage(input_tokens=10, output_tokens=5, cache_read_input_tokens=3, latency_s=1.0)
        b = Usage(input_tokens=20, output_tokens=7, cache_creation_input_tokens=4, latency_s=2.5)
        total = a + b

        assert total.input_tokens == 30
        assert total.output_tokens == 12
        assert total.cache_read_input_tokens == 3
        assert total.cache_creation_input_tokens == 4
        assert total.latency_s == 3.5

    def test_model_id_survives_addition(self):
        assert (Usage(model_id="haiku") + Usage()).model_id == "haiku"
        assert (Usage() + Usage(model_id="sonnet")).model_id == "sonnet"


class _FakeResponse:
    def __init__(self, payload: dict, status_code: int = 200, headers: dict | None = None):
        self._payload = payload
        self.status_code = status_code
        self.headers = headers or {}

    def raise_for_status(self) -> None:
        if self.status_code >= 400:
            raise RuntimeError(f"HTTP {self.status_code}")

    def json(self) -> dict:
        return self._payload


class _FakeClient:
    """Captures the request the adapter builds, and returns a canned body.

    The captured request matters as much as the parsed response here: the
    provider-specific knobs (token_param, send_temperature, extra_body)
    exist precisely so a wrong request shape can be fixed in config, so a
    regression in how they are assembled would be invisible in the reply.
    """

    sent: ClassVar[dict] = {}

    def __init__(self, payload: dict):
        self._payload = payload

    def __call__(self, *args, **kwargs):
        return self

    async def __aenter__(self):
        return self

    async def __aexit__(self, *exc):
        return False

    async def post(self, url, headers=None, json=None):
        type(self).sent = {"url": url, "headers": headers or {}, "json": json or {}}
        return _FakeResponse(self._payload)


def _run_openai(monkeypatch, payload: dict, **kwargs):
    import asyncio

    import httpx

    from resume_screener.core.router import OpenAICompatibleModel

    monkeypatch.setattr(httpx, "AsyncClient", _FakeClient(payload))
    model = OpenAICompatibleModel(
        kwargs.pop("model_id", "some-model"),
        "test-key",
        kwargs.pop("base_url", "https://example.invalid/v1"),
        **kwargs,
    )
    return asyncio.run(model.complete("SYSTEM", "USER", max_tokens=512))


_OK = {
    "choices": [{"message": {"content": '{"score": 7}'}, "finish_reason": "stop"}],
    "usage": {"prompt_tokens": 100, "completion_tokens": 20},
}


class TestOpenAICompatibleModel:
    def test_parses_text_and_usage(self, monkeypatch):
        response = _run_openai(monkeypatch, _OK)
        assert response.text == '{"score": 7}'
        assert response.usage.input_tokens == 100
        assert response.usage.output_tokens == 20
        assert response.truncated is False

    def test_cached_tokens_are_not_double_counted(self, monkeypatch):
        # Providers report cached tokens INSIDE prompt_tokens. Leaving them
        # there would bill cache reads at the full input rate, which is the
        # same class of error that inflated every cost figure in this repo
        # before the 2026-08-27 pricing fix.
        payload = {
            "choices": [{"message": {"content": "ok"}, "finish_reason": "stop"}],
            "usage": {
                "prompt_tokens": 100,
                "completion_tokens": 5,
                "prompt_tokens_details": {"cached_tokens": 80},
            },
        }
        response = _run_openai(monkeypatch, payload)
        assert response.usage.input_tokens == 20
        assert response.usage.cache_read_input_tokens == 80

    def test_never_reports_negative_input_tokens(self, monkeypatch):
        payload = {
            "choices": [{"message": {"content": "ok"}}],
            "usage": {
                "prompt_tokens": 10,
                "completion_tokens": 1,
                "prompt_tokens_details": {"cached_tokens": 50},
            },
        }
        assert _run_openai(monkeypatch, payload).usage.input_tokens == 0

    def test_joins_list_shaped_content(self, monkeypatch):
        payload = {
            "choices": [
                {"message": {"content": [{"text": '{"score":'}, {"text": " 7}"}]}}
            ],
            "usage": {},
        }
        assert _run_openai(monkeypatch, payload).text == '{"score": 7}'

    def test_marks_truncation(self, monkeypatch):
        payload = {
            "choices": [{"message": {"content": '{"score"'}, "finish_reason": "length"}],
            "usage": {},
        }
        assert _run_openai(monkeypatch, payload).truncated is True

    def test_missing_usage_does_not_crash(self, monkeypatch):
        payload = {"choices": [{"message": {"content": "ok"}}]}
        assert _run_openai(monkeypatch, payload).usage.input_tokens == 0

    def test_null_content_becomes_empty_string(self, monkeypatch):
        # A refusal or a pure-reasoning turn can return content: null.
        # Callers treat "" as a parse failure and fall back, which is right;
        # returning None would raise inside the JSON parser instead.
        payload = {"choices": [{"message": {"content": None}}], "usage": {}}
        assert _run_openai(monkeypatch, payload).text == ""

    def test_no_choices_does_not_crash(self, monkeypatch):
        assert _run_openai(monkeypatch, {"choices": [], "usage": {}}).text == ""

    def test_sends_max_tokens_by_default(self, monkeypatch):
        _run_openai(monkeypatch, _OK)
        assert _FakeClient.sent["json"]["max_tokens"] == 512
        assert "max_completion_tokens" not in _FakeClient.sent["json"]

    def test_token_param_can_be_renamed(self, monkeypatch):
        _run_openai(monkeypatch, _OK, token_param="max_completion_tokens")
        assert _FakeClient.sent["json"]["max_completion_tokens"] == 512
        assert "max_tokens" not in _FakeClient.sent["json"]

    def test_temperature_can_be_suppressed(self, monkeypatch):
        # Several reasoning models reject temperature at ANY value, so
        # omitting it has to be possible without editing code.
        _run_openai(monkeypatch, _OK, send_temperature=False)
        assert "temperature" not in _FakeClient.sent["json"]

    def test_temperature_defaults_to_zero(self, monkeypatch):
        _run_openai(monkeypatch, _OK)
        assert _FakeClient.sent["json"]["temperature"] == 0.0

    def test_extra_body_is_merged(self, monkeypatch):
        _run_openai(monkeypatch, _OK, extra_body={"reasoning_effort": "medium"})
        assert _FakeClient.sent["json"]["reasoning_effort"] == "medium"

    def test_builds_chat_completions_url_and_auth(self, monkeypatch):
        _run_openai(monkeypatch, _OK, base_url="https://example.invalid/v1/")
        assert _FakeClient.sent["url"] == "https://example.invalid/v1/chat/completions"
        assert _FakeClient.sent["headers"]["Authorization"] == "Bearer test-key"

    def test_system_and_user_stay_separate(self, monkeypatch):
        # The caching contract in core/pipeline.py depends on the system
        # string being exactly the cacheable prefix. Collapsing the two
        # turns would break that contract silently for every provider.
        _run_openai(monkeypatch, _OK)
        messages = _FakeClient.sent["json"]["messages"]
        assert messages[0] == {"role": "system", "content": "SYSTEM"}
        assert messages[1] == {"role": "user", "content": "USER"}


class _SequenceClient(_FakeClient):
    """Returns a scripted sequence of responses, one per POST.

    Retry logic is the kind of code that looks obviously correct and
    silently does nothing -- a live Gemini run lost all 20 resumes to 429s
    before this existed, so the retry path is tested rather than assumed.
    """

    def __init__(self, responses: list):
        self._responses = list(responses)
        self.attempts = 0

    def __call__(self, *args, **kwargs):
        return self

    async def post(self, url, headers=None, json=None):
        self.attempts += 1
        item = self._responses[min(self.attempts - 1, len(self._responses) - 1)]
        if isinstance(item, Exception):
            raise item
        return item


def _run_with_client(monkeypatch, client, **kwargs):
    import asyncio

    import httpx

    from resume_screener.core.router import OpenAICompatibleModel

    monkeypatch.setattr(httpx, "AsyncClient", client)
    # Near-zero backoff so the tests do not actually wait out the schedule.
    kwargs.setdefault("backoff_base", 0.0)
    kwargs.setdefault("backoff_max", 0.0)
    model = OpenAICompatibleModel(
        "some-model", "test-key", "https://example.invalid/v1", **kwargs
    )
    return asyncio.run(model.complete("SYSTEM", "USER"))


class TestOpenAICompatibleRetry:
    def test_retries_429_then_succeeds(self, monkeypatch):
        client = _SequenceClient(
            [_FakeResponse({}, 429), _FakeResponse({}, 429), _FakeResponse(_OK)]
        )
        response = _run_with_client(monkeypatch, client)
        assert client.attempts == 3
        assert response.text == '{"score": 7}'

    def test_retries_server_errors(self, monkeypatch):
        client = _SequenceClient([_FakeResponse({}, 503), _FakeResponse(_OK)])
        assert _run_with_client(monkeypatch, client).text == '{"score": 7}'
        assert client.attempts == 2

    def test_does_not_retry_client_errors(self, monkeypatch):
        # A 400 means the request is wrong -- a bad model id, a rejected
        # parameter. Retrying it burns quota and hides the real cause.
        client = _SequenceClient([_FakeResponse({"error": "bad model"}, 400)])
        with pytest.raises(RuntimeError):
            _run_with_client(monkeypatch, client)
        assert client.attempts == 1

    def test_gives_up_after_max_retries(self, monkeypatch):
        client = _SequenceClient([_FakeResponse({}, 429)])
        with pytest.raises(RuntimeError):
            _run_with_client(monkeypatch, client, max_retries=2)
        assert client.attempts == 3  # first try + 2 retries

    def test_retries_transport_errors(self, monkeypatch):
        import httpx

        client = _SequenceClient(
            [httpx.ConnectError("connection reset"), _FakeResponse(_OK)]
        )
        assert _run_with_client(monkeypatch, client).text == '{"score": 7}'
        assert client.attempts == 2

    def test_transport_error_propagates_when_retries_exhausted(self, monkeypatch):
        import httpx

        client = _SequenceClient([httpx.ConnectError("connection reset")])
        with pytest.raises(httpx.ConnectError):
            _run_with_client(monkeypatch, client, max_retries=1)
        assert client.attempts == 2

    def test_honours_retry_after_header(self, monkeypatch):
        from resume_screener.core import router

        slept: list[float] = []

        async def fake_sleep(seconds):
            slept.append(seconds)

        monkeypatch.setattr(router.asyncio, "sleep", fake_sleep, raising=False)
        client = _SequenceClient(
            [_FakeResponse({}, 429, {"Retry-After": "30"}), _FakeResponse(_OK)]
        )
        _run_with_client(monkeypatch, client, backoff_base=1.0, backoff_max=60.0)
        # Full jitter halves it at most, so a 30s instruction must not
        # produce a delay shorter than 15s.
        assert slept and 15.0 <= slept[0] <= 30.0

    def test_ignores_unparseable_retry_after(self, monkeypatch):
        client = _SequenceClient(
            [_FakeResponse({}, 429, {"Retry-After": "Wed, 21 Oct 2026 07:28:00 GMT"}),
             _FakeResponse(_OK)]
        )
        assert _run_with_client(monkeypatch, client).text == '{"score": 7}'


class TestRetryDelayParsing:
    """Google sends no Retry-After header; the delay is in the error body.

    A header-only reader falls back to its own guess against the one
    provider in this bake-off most likely to throttle, which is exactly
    where honouring the provider matters most.
    """

    def test_prefers_retry_after_header(self):
        from resume_screener.core.router import _retry_delay_from

        resp = _FakeResponse({"error": {"message": "retry in 9s"}}, 429, {"Retry-After": "3"})
        assert _retry_delay_from(resp) == "3"

    def test_reads_google_style_message_body(self):
        from resume_screener.core.router import _retry_delay_from

        body = {
            "error": {
                "code": 429,
                "message": "Quota exceeded. Please retry in 4.613214581s.",
            }
        }
        assert _retry_delay_from(_FakeResponse(body, 429)) == "4.613214581"

    def test_reads_body_wrapped_in_a_list(self):
        # Google returned the error object inside a JSON array.
        from resume_screener.core.router import _retry_delay_from

        body = [{"error": {"message": "Please retry in 12s."}}]
        assert _retry_delay_from(_FakeResponse(body, 429)) == "12"

    def test_returns_none_when_no_delay_offered(self):
        from resume_screener.core.router import _retry_delay_from

        assert _retry_delay_from(_FakeResponse({"error": {"message": "slow down"}}, 429)) is None

    def test_survives_a_non_json_body(self):
        from resume_screener.core.router import _retry_delay_from

        class Bad(_FakeResponse):
            def json(self):
                raise ValueError("not json")

        assert _retry_delay_from(Bad({}, 429)) is None


class _FakeAnthropicClient:
    """Minimal stand-in for AsyncAnthropic, capturing the messages sent."""

    def __init__(self, text: str):
        self._text = text
        self.sent: dict = {}
        self.messages = self

    async def create(self, **kwargs):
        self.sent = kwargs

        class _Usage:
            input_tokens = 10
            output_tokens = 5
            cache_creation_input_tokens = 0
            cache_read_input_tokens = 0

        class _Response:
            content: ClassVar[list] = [Block("text", self._text)]
            usage = _Usage()
            stop_reason = "end_turn"

        return _Response()


def _anthropic_with(monkeypatch, text: str, **kwargs):
    import asyncio

    from resume_screener.core import router

    fake = _FakeAnthropicClient(text)
    model = router.AnthropicModel.__new__(router.AnthropicModel)
    model._model_id = "claude-test"
    model._client = fake
    model._prefill = kwargs.get("prefill", "")
    return asyncio.run(model.complete("SYSTEM", "USER")), fake


class TestAnthropicPrefill:
    """Prefill is the knob that tests section 8a's own hypothesis -- that
    Haiku's 49% unparseable rate was a structured-output problem. If the
    prefix is not stitched back on, every response loses its opening brace
    and the parse failures get worse, not better."""

    def test_no_prefill_sends_only_the_user_turn(self, monkeypatch):
        response, fake = _anthropic_with(monkeypatch, '{"score": 7}')
        assert [m["role"] for m in fake.sent["messages"]] == ["user"]
        assert response.text == '{"score": 7}'

    def test_prefill_appends_an_assistant_turn(self, monkeypatch):
        _, fake = _anthropic_with(monkeypatch, '"score": 7}', prefill="{")
        assert [m["role"] for m in fake.sent["messages"]] == ["user", "assistant"]
        assert fake.sent["messages"][1]["content"] == "{"

    def test_prefill_is_stitched_back_onto_the_reply(self, monkeypatch):
        # The API does not echo the prefill, so without this the caller
        # gets '"score": 7}' -- unparseable, and silently so.
        response, _ = _anthropic_with(monkeypatch, '"score": 7}', prefill="{")
        assert response.text == '{"score": 7}'
        assert json.loads(response.text) == {"score": 7}

    def test_system_block_is_unchanged_by_prefill(self, monkeypatch):
        # The caching contract keys on the system string. Prefill must not
        # touch it, or every cached prefix is invalidated.
        _, fake = _anthropic_with(monkeypatch, "{}", prefill="{")
        assert fake.sent["system"][0]["text"] == "SYSTEM"
