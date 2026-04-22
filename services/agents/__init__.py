"""Per-platform takedown agents.

Each agent knows how to shape a notice for one platform. The top-level
backend.takedown.draft_notice() delegates to the agent registered for the
candidate's platform. This module preserves the "agent per platform" framing
from the Pramāṇ plan while keeping the implementation single-process; if the
ADK-style out-of-process multi-agent orchestration comes back, the interface
below is the drop-in surface for it.
"""

from __future__ import annotations

from backend.schema import Candidate, Clip, Jurisdiction, VerdictRecord

from services.agents.base import PlatformAgent
from services.agents.meta_agent import MetaAgent
from services.agents.telegram_agent import TelegramAgent
from services.agents.x_agent import XAgent
from services.agents.youtube_agent import YouTubeAgent

_REGISTRY: dict[str, PlatformAgent] = {
    "x":        XAgent(),
    "youtube":  YouTubeAgent(),
    "meta":     MetaAgent(),
    "telegram": TelegramAgent(),
}


def get(platform: str) -> PlatformAgent:
    """Return the agent for a platform, or a safe fallback for unknown ones."""
    return _REGISTRY.get(platform, XAgent())  # DMCA §512(c) shape is the safe default.


__all__ = ["PlatformAgent", "get"]
