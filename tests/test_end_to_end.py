"""End-to-end integration test for Aegis, LOCAL mode (no GCP).

Walks the flagship demo scenario as a test so regressions surface on CI:

    publish -> ingest     -> C2PA manifest + fingerprints + Merkle-anchor leaf
    leak    -> detect     -> classifier verdict + Merkle-anchor leaf
    respond -> takedown   -> platform agent draft + mock-endpoint filed + Merkle-anchor leaf
    verify  -> /verify    -> Merkle-anchored receipt with valid signature

Run:
    pytest tests/test_end_to_end.py -v

Requires ffmpeg on PATH for keyframe extraction. Does not require a GCP project.
"""

from __future__ import annotations

import shutil
import subprocess
from pathlib import Path

import pytest
from fastapi.testclient import TestClient


pytestmark = pytest.mark.skipif(
    shutil.which("ffmpeg") is None,
    reason="ffmpeg not installed",
)


@pytest.fixture
def client(tmp_path, monkeypatch):
    # The autouse conftest fixture already forces LOCAL mode + clears
    # Gemini / VERTEX env. Here we only pin the workdir and strip stale mock
    # endpoints so the takedown notice stays DRAFT (exercising the "mock
    # endpoint unset" tolerance path).
    monkeypatch.setenv("AEGIS_WORKDIR", str(tmp_path / "aegis"))
    for k in ("MOCK_X_ENDPOINT", "MOCK_YOUTUBE_ENDPOINT", "MOCK_META_ENDPOINT", "MOCK_TELEGRAM_ENDPOINT"):
        monkeypatch.delenv(k, raising=False)
    from backend.main import app
    return TestClient(app)


def _synthesize_clip(path: Path, source: str) -> Path:
    """Produce a deterministic 2s MP4 from an ffmpeg lavfi source."""
    subprocess.run(
        [
            "ffmpeg", "-y", "-loglevel", "error",
            "-f", "lavfi", "-i", f"{source}=duration=2:size=320x240:rate=10",
            "-c:v", "libx264", "-pix_fmt", "yuv420p", str(path),
        ],
        check=True,
    )
    return path


@pytest.fixture(scope="module")
def sample_clip(tmp_path_factory) -> Path:
    """Canonical sample clip used as the 'original' in the pipeline test."""
    return _synthesize_clip(tmp_path_factory.mktemp("clip") / "sample.mp4", "testsrc")


@pytest.fixture(scope="module")
def unrelated_clip(tmp_path_factory) -> Path:
    """A visually unrelated clip used to exercise the below-threshold path.

    `smptebars` and `testsrc` produce pHash / embedding signatures that are
    far apart, so detection should return matched=false — i.e. no verdict and
    no draft takedown. If this assumption changes, the test tells us.
    """
    return _synthesize_clip(tmp_path_factory.mktemp("clip2") / "unrelated.mp4", "smptebars")


def test_health(client):
    r = client.get("/healthz")
    assert r.status_code == 200
    assert r.json()["ok"] is True


def test_full_pipeline(client, sample_clip):
    # 1. Ingest.
    with sample_clip.open("rb") as f:
        r = client.post(
            "/ingest",
            data={
                "title":                  "Test-Subject Meera vs Test-League",
                "sport":                  "cricket",
                "event":                  "Test-League 2026 Match 1",
                "rights_holder":          "Test-League Broadcasting (fictional)",
                "rights_holder_name":     "Integration Test Operator",
                "rights_holder_title":    "Operator",
                "rights_holder_address":  "N/A",
                "rights_holder_phone":    "+0-000-000-0000",
                "rights_holder_email":    "ops@test.aegis.test",
                "athletes_csv":           "test-subject-meera",
            },
            files={"video": (sample_clip.name, f, "video/mp4")},
        )
    assert r.status_code == 200, r.text
    clip_id = r.json()["clip_id"]

    # 2. Detect — submit the same clip as the candidate. Deterministic mock
    #    verdict returns EXACT_PIRACY at high confidence for high hash sim.
    with sample_clip.open("rb") as f:
        r = client.post(
            "/detect",
            data={
                "candidate_url": "https://aegis-test-domain.example/leak.mp4",
                "platform":      "x",
                "uploader":      "pirate-bot-1",
                "caption":       "leaked clip",
                "host_country":  "IN",
            },
            files={"video": (sample_clip.name, f, "video/mp4")},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["matched"] is True, body
    detection_id = body["verdict"]["detection_id"]
    # AEGIS_DEMO_MODE is off in tests, caption is "leaked clip" — the
    # deterministic mock rule gives EXACT_PIRACY. Tighten assertion.
    assert body["verdict"]["verdict"] == "EXACT_PIRACY", body

    # 3. Takedown — draft; mock endpoint unset so status stays DRAFT.
    #    This step is the regression guard for the v2 Candidate-persistence bug:
    #    if /detect forgets to store.put_candidate(...), /takedown 404s here.
    r = client.post("/takedown", json={"detection_id": detection_id, "file_now": True})
    assert r.status_code != 404, f"Candidate not persisted (regression): {r.text}"
    assert r.status_code in (200, 409), r.text
    if r.status_code == 200:
        notice = r.json()["notice"]
        assert notice["jurisdiction"] in ("IN", "US", "OTHER")
        assert "Aegis detection" in notice["body"] or "detection" in notice["body"].lower()

    # 4. Verify — should have a Merkle receipt because anchor_mode is EAGER.
    r = client.get(f"/verify/{detection_id}")
    assert r.status_code == 200
    v = r.json()
    assert v["detection_id"] == detection_id
    assert v["merkle_receipt"] is not None, v
    receipt = v["merkle_receipt"]
    assert receipt["leaf_count"] >= 1
    assert len(receipt["merkle_root_hex"]) == 64


def test_below_threshold_does_not_file(client, sample_clip, unrelated_clip):
    """Takedown restraint: an unrelated candidate must not reach Stage 2 or file a notice."""
    # Step 1: ingest the sample so there's at least one clip in the index.
    with sample_clip.open("rb") as f:
        r = client.post(
            "/ingest",
            data={
                "title": "unrelated-baseline", "sport": "cricket",
                "event": "Test 2026", "rights_holder": "rh",
                "rights_holder_name": "n", "rights_holder_title": "t",
                "rights_holder_address": "a", "rights_holder_phone": "p",
                "rights_holder_email": "e@e.test", "athletes_csv": "",
            },
            files={"video": (sample_clip.name, f, "video/mp4")},
        )
    assert r.status_code == 200, r.text

    # Step 2: submit a visually-unrelated clip — Stage 1 must NOT escalate.
    with unrelated_clip.open("rb") as f:
        r = client.post(
            "/detect",
            data={
                "candidate_url": "https://aegis-test-domain.example/unrelated.mp4",
                "platform":      "meta",
                "uploader":      "fan",
                "caption":       "general sports reaction",
                "host_country":  "US",
            },
            files={"video": (unrelated_clip.name, f, "video/mp4")},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    # The key assertion: below-threshold returns matched=false (no verdict
    # created, no notice drafted, no leaf appended). This is the ethics
    # guardrail the deck cites as "takedown restraint."
    assert body.get("matched") is False, body


def test_demo_mode_caption_triggers_deepfake(client, sample_clip, monkeypatch):
    """Caption-keyword rule for DEEPFAKE_MANIPULATION is gated on AEGIS_DEMO_MODE."""
    monkeypatch.setenv("AEGIS_DEMO_MODE", "true")

    # Ingest the baseline so Stage 1 retrieval has something to match.
    with sample_clip.open("rb") as f:
        client.post(
            "/ingest",
            data={
                "title": "demo-mode", "sport": "cricket",
                "event": "Test 2026", "rights_holder": "rh",
                "rights_holder_name": "n", "rights_holder_title": "t",
                "rights_holder_address": "a", "rights_holder_phone": "p",
                "rights_holder_email": "e@e.test", "athletes_csv": "test-subject-meera",
            },
            files={"video": (sample_clip.name, f, "video/mp4")},
        ).raise_for_status()

    with sample_clip.open("rb") as f:
        r = client.post(
            "/detect",
            data={
                "candidate_url": "https://aegis-test-domain.example/meera-deepfake.mp4",
                "platform":      "telegram",
                "uploader":      "bad-actor",
                "caption":       "Test-Subject Meera — deepfake / morphed clip",
                "host_country":  "IN",
            },
            files={"video": (sample_clip.name, f, "video/mp4")},
        )
    assert r.status_code == 200, r.text
    body = r.json()
    assert body["matched"] is True
    assert body["verdict"]["verdict"] == "DEEPFAKE_MANIPULATION"
    assert body["verdict"]["athlete_alert"]["should_alert"] is True


def test_demo_status_reports_local_mode(client):
    r = client.get("/demo/status")
    assert r.status_code == 200
    s = r.json()
    assert s["index_mode"] == "LOCAL"
    assert s["gemini_live"] is False
    assert s["demo_mode"] is False


def test_anchor_flush_returns_receipt_count(client):
    r = client.post("/provenance/anchor")
    assert r.status_code == 200
    body = r.json()
    assert "flushed" in body
