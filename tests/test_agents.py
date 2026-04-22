"""Unit tests for platform agents and jurisdiction routing."""

from __future__ import annotations

import os
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


def test_unknown_platform_falls_back_to_other_or_us():
    c = _mk_candidate("unknown_platform_zzz")
    j = pick_jurisdiction(c)
    assert j in (Jurisdiction.OTHER, Jurisdiction.US)  # fallback agent is XAgent -> US


def test_agent_submit_endpoint_resolves_from_env():
    os.environ["MOCK_X_ENDPOINT"] = "http://localhost:8101/takedown"
    try:
        assert get_agent("x").resolve_submit_endpoint() == "http://localhost:8101/takedown"
    finally:
        os.environ.pop("MOCK_X_ENDPOINT", None)


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
