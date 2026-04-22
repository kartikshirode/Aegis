"""Unit tests for platform agents and jurisdiction routing."""

from __future__ import annotations

from datetime import datetime, timezone

import pytest

from backend.schema import Candidate, CandidateHashMatch, Jurisdiction, Verdict, VerdictRecord, Action, AthleteAlert
from backend.takedown import pick_jurisdiction
from services.agents import get as get_agent


def _mk_candidate(platform: str, host_country: str | None = None, caption: str = "") -> Candidate:
    return Candidate(
        candidate_id="cand-1",
        url="https://example.com/clip.mp4",
        platform=platform,  # type: ignore[arg-type]
        host_country=host_country,
        uploader="u",
        caption=caption,
        found_at=datetime.now(timezone.utc),
        storage_uri="/tmp/x",
        hash_match=CandidateHashMatch(phash_distance=5, embedding_cosine=0.9),
    )


def test_x_agent_defaults_to_us():
    assert pick_jurisdiction(_mk_candidate("x")) == Jurisdiction.US


def test_youtube_in_host_country_overrides_to_india():
    assert pick_jurisdiction(_mk_candidate("youtube", host_country="IN")) == Jurisdiction.IN


def test_telegram_with_indian_caption_prefers_india():
    c = _mk_candidate("telegram", host_country=None, caption="IPL 2026 clip")
    assert pick_jurisdiction(c) == Jurisdiction.IN


def test_schema_rejects_unknown_platform_strings():
    # First line of defence: Candidate.platform is a Literal, so arbitrary typos
    # never reach the agent registry. This guards against the "platfrom=telegrum"
    # scenario from audit v2 at the API boundary.
    import pytest
    with pytest.raises(Exception):
        _mk_candidate("unknown_platform_zzz")


def test_schema_allowed_but_unregistered_platform_routes_to_generic():
    # `other` and `mock` are allowed by the Literal but have no explicit agent.
    # They must NOT silently borrow XAgent's DMCA-to-Twitter envelope —
    # they route to GenericAgent with OTHER jurisdiction.
    c_other = _mk_candidate("other")
    assert pick_jurisdiction(c_other) == Jurisdiction.OTHER

    c_other_in = _mk_candidate("other", host_country="IN")
    assert pick_jurisdiction(c_other_in) == Jurisdiction.IN


def test_generic_agent_provider_is_placeholder_not_twitter():
    from services.agents import get as get_agent
    agent = get_agent("other")
    assert "twitter" not in agent.designated_agent_email().lower()
    assert "[" in agent.host_provider()  # placeholder bracket style


def test_agent_submit_endpoint_resolves_from_env(monkeypatch):
    monkeypatch.setenv("MOCK_X_ENDPOINT", "http://localhost:8101/takedown")
    assert get_agent("x").resolve_submit_endpoint() == "http://localhost:8101/takedown"


def test_deepfake_rule_basis_includes_rule_3_2_b():
    v = VerdictRecord(
        detection_id="d",
        original_clip_id="o",
        candidate_id="c",
        verdict=Verdict.DEEPFAKE_MANIPULATION,
        confidence=0.9,
        evidence=[],
        recommended_action=Action.ATHLETE_ALERT_AND_TAKEDOWN,
        athlete_alert=AthleteAlert(should_alert=True, reason="synthetic"),
        created_at=datetime.now(timezone.utc),
    )
    basis = get_agent("telegram").rule_basis_for(v)
    assert "Rule 3(2)(b)" in basis
