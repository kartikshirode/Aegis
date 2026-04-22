from backend.schema import Candidate, Jurisdiction

from services.agents.base import PlatformAgent


class XAgent(PlatformAgent):
    platform = "x"
    display_name = "X (Twitter)"
    default_jurisdiction = Jurisdiction.US
    sla_hours_default = 24
    submit_endpoint_env = "MOCK_X_ENDPOINT"

    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction:
        if candidate.host_country == "IN":
            return Jurisdiction.IN
        return Jurisdiction.US

    def host_provider(self) -> str:
        return "X Corp."

    def designated_agent_email(self) -> str:
        return "copyright@twitter.com"
