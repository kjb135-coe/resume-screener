"""Extension point for consuming external MCP servers (client role).

Not wired into the pipeline or the demo -- see README, "Scope decisions".
This module documents the shape a real integration would take (e.g. a
GitHub MCP server verifying a candidate's claimed profile, or a company
lookup server) without depending on any external service being live.
"""

from __future__ import annotations

from typing import Protocol


class EnrichmentSource(Protocol):
    """Anything that can add corroborating signal for one candidate.

    A real implementation would wrap an `mcp.Client` pointed at an
    external server (see the MCP Python SDK's Client class) and translate
    its tool calls into a plain dict the pipeline can fold into evidence.
    """

    async def enrich(self, candidate_name: str, claim: str) -> dict: ...
