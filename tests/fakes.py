"""A scripted Model implementation so the pipeline can be tested offline.

Tests must never hit the real API: it costs money, needs a key, and makes
results non-deterministic. This returns canned responses keyed by which
tier is calling, and records every call for assertions.
"""

from __future__ import annotations

import json

from resume_screener.core.router import Model, ModelResponse, Usage


class FakeModel(Model):
    def __init__(self, responses: list[str], *, model_id: str = "fake"):
        self._responses = list(responses)
        self._model_id = model_id
        self.calls: list[dict] = []

    async def complete(
        self,
        system: str,
        user: str,
        *,
        max_tokens: int = 1024,
        cache_system: bool = True,
    ) -> ModelResponse:
        self.calls.append(
            {
                "system": system,
                "user": user,
                "cache_system": cache_system,
            }
        )
        text = self._responses[min(len(self.calls) - 1, len(self._responses) - 1)]
        return ModelResponse(
            text=text,
            usage=Usage(
                input_tokens=100,
                output_tokens=20,
                cache_read_input_tokens=80 if cache_system and len(self.calls) > 1 else 0,
                cache_creation_input_tokens=80 if cache_system and len(self.calls) == 1 else 0,
                latency_s=0.01,
                model_id=self._model_id,
            ),
        )


EXTRACTION_JSON = json.dumps(
    {
        "name": "Jane Doe",
        "years_experience": 7,
        "companies": ["Acme Corp", "Beta Inc"],
        "technologies": ["Python", "FastAPI", "MCP", "AWS"],
        "education": ["BS Computer Science"],
        "evidence": [
            {
                "quote": "Built and shipped an agentic document-processing system to production serving 12,000 requests/day",
                "rubric_dimension": "production_reality",
            },
            {
                "quote": "Presented quarterly architecture reviews to non-technical stakeholders",
                "rubric_dimension": "client_communication",
            },
        ],
        "confidence": 0.9,
    }
)


def panel_json(score: float, rationale: str = "Solid evidence.") -> str:
    return json.dumps({"score": score, "confidence": 0.8, "rationale": rationale})


def arbiter_json(score: float, recommendation: str = "advance") -> str:
    return json.dumps(
        {"score": score, "recommendation": recommendation, "rationale": "Arbiter resolved."}
    )


def rubric_json(names: list[str] | None = None) -> str:
    """A well-formed rubric-generator response.

    Defaults to the same three dimension names the hand-written rubric
    uses, so tests can swap a generated rubric in for the static one and
    compare like with like.
    """
    names = names or ["production_reality", "technical_integration", "client_communication"]
    return json.dumps(
        {
            "role_title": "AI Solutions Engineer",
            "summary": "Wants production-shipped agentic systems, not research or demos.",
            "dimensions": [
                {
                    "name": name,
                    "title": name.replace("_", " ").title(),
                    "criteria": f"Score the evidence for {name}. Demo-stage work scores low.",
                    "lens": f"You judge {name} only. Ignore every other dimension.",
                }
                for name in names
            ],
        }
    )
