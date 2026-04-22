"""PlatformAgent interface.

One agent per platform. Each agent:
  - picks the jurisdiction (IN / US / OTHER) for the candidate,
  - selects the matching prompt template (IT Rules 2021 / DMCA §512(c)),
  - formats a detection record that the Gemini fill-in step expects,
  - produces the submit payload, knowing the platform's envelope quirks.
"""

from __future__ import annotations

import os
from abc import ABC, abstractmethod
from dataclasses import dataclass

from backend.schema import Candidate, Clip, Jurisdiction, VerdictRecord


@dataclass
class AgentContext:
    original: Clip
    candidate: Candidate
    verdict: VerdictRecord
    affected_person: dict | None


class PlatformAgent(ABC):
    platform: str
    display_name: str
    default_jurisdiction: Jurisdiction
    sla_hours_default: int
    submit_endpoint_env: str  # env var that holds the submit URL

    @abstractmethod
    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction: ...

    @abstractmethod
    def host_provider(self) -> str: ...

    @abstractmethod
    def designated_agent_email(self) -> str: ...

    def resolve_submit_endpoint(self) -> str | None:
        return os.environ.get(self.submit_endpoint_env)

    def rule_basis_for(self, verdict: VerdictRecord) -> list[str]:
        """Default mapping — individual platforms may override (e.g. Telegram de-emphasises DMCA)."""
        v = verdict.verdict.value
        if v == "DEEPFAKE_MANIPULATION":
            return ["Rule 3(2)(b)", "Rule 3(1)(b)(vii)"]
        if v in ("EXACT_PIRACY", "SCREEN_RECORDING"):
            return ["copyright"]
        return []
