from backend.schema import Candidate, Jurisdiction

from services.agents.base import PlatformAgent


class GenericAgent(PlatformAgent):
    """Fallback for unknown platforms.

    Produces a jurisdiction-aware notice with a clearly-marked placeholder for
    the host provider and designated agent. This keeps typos and unrecognised
    platforms from silently borrowing another platform's envelope — an audit-v2
    design concern. A notice with placeholders is visibly wrong; a notice with
    the wrong provider in it is silently wrong.
    """

    platform = "generic"
    display_name = "[unknown platform]"
    default_jurisdiction = Jurisdiction.OTHER
    sla_hours_default = 72
    submit_endpoint_env = "MOCK_GENERIC_ENDPOINT"

    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction:
        if candidate.host_country == "IN":
            return Jurisdiction.IN
        if candidate.host_country == "US":
            return Jurisdiction.US
        return Jurisdiction.OTHER

    def host_provider(self) -> str:
        return "[host provider — platform not recognised by Aegis agent registry]"

    def designated_agent_email(self) -> str:
        return "[designated agent — consult platform's published DMCA / IT Rules policy]"
