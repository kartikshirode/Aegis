from backend.schema import Candidate, Jurisdiction

from services.agents.base import PlatformAgent


class YouTubeAgent(PlatformAgent):
    platform = "youtube"
    display_name = "YouTube"
    default_jurisdiction = Jurisdiction.US
    sla_hours_default = 72
    submit_endpoint_env = "MOCK_YOUTUBE_ENDPOINT"

    def pick_jurisdiction(self, candidate: Candidate) -> Jurisdiction:
        if candidate.host_country == "IN":
            return Jurisdiction.IN
        return Jurisdiction.US

    def host_provider(self) -> str:
        return "Google LLC (YouTube)"

    def designated_agent_email(self) -> str:
        return "copyright@youtube.com"
