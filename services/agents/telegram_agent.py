from backend.schema import Candidate, Jurisdiction, VerdictRecord

from services.agents.base import PlatformAgent


class TelegramAgent(PlatformAgent):
    """Telegram agent.

    Telegram's public abuse and takedown flows are less uniform than DMCA or the
    IT Rules. For Indian-facing channels we preferentially route under IT Rules
    2021 + MeitY Nov 2023 advisory, since those are the levers with the
    strongest practical traction against cricket-piracy mirror networks.
    """

    platform = "telegram"
    display_name = "Telegram"
    default_jurisdiction = Jurisdiction.OTHER
    sla_hours_default = 72
    submit_endpoint_env = "MOCK_TELEGRAM_ENDPOINT"

    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction:
        # If we have an India signal, prefer IT Rules; else fall back to the
        # DMCA-shaped template since it's the most universally recognised.
        if candidate.host_country == "IN" or _looks_indian(candidate):
            return Jurisdiction.IN
        if candidate.host_country == "US":
            return Jurisdiction.US
        return Jurisdiction.OTHER  # takedown.py maps OTHER -> DMCA template

    def host_provider(self) -> str:
        return "Telegram FZ-LLC"

    def designated_agent_email(self) -> str:
        return "dmca@telegram.org"

    def rule_basis_for(self, verdict: VerdictRecord) -> list[str]:
        # Same defaults; kept overridable for platform-specific nuance.
        return super().rule_basis_for(verdict)


def _looks_indian(candidate: Candidate) -> bool:
    caption = (candidate.caption or "").lower()
    indicators = ("ipl", "bcci", "jio", "hotstar", "dd sports", "star sports")
    return any(i in caption for i in indicators)
