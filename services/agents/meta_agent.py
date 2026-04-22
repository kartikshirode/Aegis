from backend.schema import Candidate, Jurisdiction

from services.agents.base import PlatformAgent


class MetaAgent(PlatformAgent):
    platform = "meta"
    display_name = "Meta (Facebook / Instagram)"
    default_jurisdiction = Jurisdiction.US
    sla_hours_default = 48
    submit_endpoint_env = "MOCK_META_ENDPOINT"

    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction:
        if candidate.host_country == "IN":
            return Jurisdiction.IN
        return Jurisdiction.US

    def host_provider(self) -> str:
        return "Meta Platforms, Inc."

    def designated_agent_email(self) -> str:
        return "ip@meta.com"
