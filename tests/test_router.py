"""Response parsing in the provider layer.

The text-block extraction is regression-tested because getting it wrong is
silent and intermittent: it only fails when the model happens to emit a
thinking block, so it can pass a smoke test and then break most of a batch.
"""

from __future__ import annotations

from dataclasses import dataclass

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
