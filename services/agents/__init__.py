"""Per-platform takedown agents.

Each agent knows how to shape a notice for one platform. The top-level
backend.takedown.draft_notice() delegates to the agent registered for the
candidate's platform. This module preserves the "agent per platform" framing
from the original design plan while keeping the implementation single-process;
if the ADK-style out-of-process multi-agent orchestration comes back, the
interface below is the drop-in surface for it.
"""

from __future__ import annotations

from services.agents.base import PlatformAgent
from services.agents.generic_agent import GenericAgent
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

_GENERIC = GenericAgent()


def get(platform: str) -> PlatformAgent:
    """Return the agent for a known platform, or a provider-unbranded GenericAgent.

    Unknown platforms MUST NOT silently borrow XAgent's DMCA-to-Twitter
    envelope — a typo like `platfrom="telegrum"` would otherwise file a
    malformed notice at `copyright@twitter.com` for a host that isn't X
    (audit v2 residual design drift).
    """
    return _REGISTRY.get(platform, _GENERIC)


__all__ = ["PlatformAgent", "get"]

