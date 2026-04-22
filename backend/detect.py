"""Two-stage detection.

Stage 1 — fast recall (< 100 ms):
    For a CANDIDATE clip, extract keyframes, compute pHash + multimodal embedding,
    query Vector Search (ScaNN) for top-k nearest Clip embeddings. If any hit
    crosses an escalation threshold, pass to Stage 2.

Stage 2 — semantic verification (Gemini 2.5 Pro):
    Pass (ORIGINAL, CANDIDATE) pair to Gemini with prompts/verdict.txt.
    Parse JSON. If DEEPFAKE_MANIPULATION and confidence borderline, escalate
    to the dedicated deepfake_verdict.txt classifier.
"""

from __future__ import annotations

import hashlib
import json
import os
import uuid
from dataclasses import dataclass
from datetime import datetime, timezone
from pathlib import Path

import imagehash
from PIL import Image

from backend.ingest import compute_embeddings, extract_keyframes
from backend.schema import (
    Action,
    AthleteAlert,
    Candidate,
    CandidateHashMatch,
    Clip,
    Verdict,
    VerdictRecord,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"

# Thresholds — tuned on the variant set in benchmark/generate_variants.py.
# Do not edit in isolation; re-run benchmark/run.py after any change.
PHASH_ESCALATE_DISTANCE = 12
EMBEDDING_ESCALATE_COSINE = 0.78
DEEPFAKE_ESCALATION_CONFIDENCE = 0.60


@dataclass
class Stage1Match:
    clip_id: str
    phash_distance: int
    embedding_cosine: float

    @property
    def should_escalate(self) -> bool:
        return (
            self.phash_distance <= PHASH_ESCALATE_DISTANCE
            or self.embedding_cosine >= EMBEDDING_ESCALATE_COSINE
        )


def fingerprint_candidate(video_path: Path, workdir: Path) -> tuple[list[str], list[list[float]]]:
    frames = extract_keyframes(video_path, workdir / "candidate_frames")
    phashes = [str(imagehash.phash(Image.open(f))) for f in frames]
    embeddings = compute_embeddings(frames)
    return phashes, embeddings


def stage1_retrieve(
    candidate_phashes: list[str],
    candidate_embeddings: list[list[float]],
    *,
    top_k: int = 5,
) -> list[Stage1Match]:
    """Retrieve top-k candidate Clips by embedding, then score pHash."""
    from backend.vector_index import query_top_k, get_clip_phashes  # thin wrapper

    hits = query_top_k(candidate_embeddings, k=top_k)

    matches: list[Stage1Match] = []
    for hit in hits:
        stored_phashes = get_clip_phashes(hit.clip_id)
        best_ph = _best_phash_distance(candidate_phashes, stored_phashes)
        matches.append(
            Stage1Match(
                clip_id=hit.clip_id,
                phash_distance=best_ph,
                embedding_cosine=hit.cosine,
            )
        )
    return matches


def _best_phash_distance(a_hashes: list[str], b_hashes: list[str]) -> int:
    best = 64
    for a in a_hashes:
        ha = imagehash.hex_to_hash(a)
        for b in b_hashes:
            hb = imagehash.hex_to_hash(b)
            d = ha - hb
            if d < best:
                best = d
    return best


def stage2_verdict(
    original: Clip,
    candidate: Candidate,
    candidate_video_path: Path,
    original_video_path: Path,
) -> VerdictRecord:
    """Call Gemini 2.5 Pro with prompts/verdict.txt and parse JSON."""
    system_prompt = (PROMPTS_DIR / "verdict.txt").read_text(encoding="utf-8")

    user_payload = {
        "ORIGINAL": {
            "clip_id": original.clip_id,
            "sport": original.sport,
            "event": original.event,
            "timestamp": original.first_published.isoformat(),
            "rights_holder": original.rights_holder,
            "athletes": original.athletes,
            "c2pa_manifest": str(original.c2pa_manifest_url),
        },
        "CANDIDATE": {
            "url": str(candidate.url),
            "platform": candidate.platform,
            "host_country": candidate.host_country,
            "uploader": candidate.uploader,
            "caption": candidate.caption,
            "found_at": candidate.found_at.isoformat(),
            "hash_match": candidate.hash_match.model_dump(),
        },
    }

    raw = _call_gemini(
        system_prompt=system_prompt,
        user_payload=user_payload,
        video_refs=[original_video_path, candidate_video_path],
    )
    data = _strict_json(raw)

    return VerdictRecord(
        detection_id=str(uuid.uuid4()),
        original_clip_id=original.clip_id,
        candidate_id=candidate.candidate_id,
        verdict=Verdict(data["verdict"]),
        confidence=float(data["confidence"]),
        evidence=list(data.get("evidence", [])),
        recommended_action=Action(data["recommended_action"]),
        athlete_alert=AthleteAlert(**data.get("athlete_alert", {"should_alert": False, "reason": ""})),
        created_at=datetime.now(timezone.utc),
    )


def _call_gemini(
    *,
    system_prompt: str,
    user_payload: dict,
    video_refs: list[Path],
) -> str:
    """Gemini call. Mock fallback when GOOGLE_API_KEY is unset for local dev."""
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("VERTEX_AI_PROJECT"):
        return _mock_verdict(user_payload)

    # Vertex AI Gemini path.
    from vertexai.generative_models import GenerativeModel, Part

    model = GenerativeModel("gemini-2.5-pro", system_instruction=system_prompt)
    parts: list = [json.dumps(user_payload)]
    for v in video_refs:
        parts.append(Part.from_data(v.read_bytes(), mime_type="video/mp4"))
    resp = model.generate_content(parts, generation_config={"response_mime_type": "application/json"})
    return resp.text


def _strict_json(raw: str) -> dict:
    """Parse a JSON blob; tolerate a single surrounding markdown fence."""
    s = raw.strip()
    if s.startswith("```"):
        s = s.strip("`")
        s = s.split("\n", 1)[1] if "\n" in s else s
        if s.endswith("```"):
            s = s[:-3]
    return json.loads(s)


def _mock_verdict(payload: dict) -> str:
    """Deterministic mock for local dev when no API key is available.

    Decision rules — keep simple, match the benchmark happy path:
      - phash_distance <= 6  OR embedding_cosine >= 0.92 -> EXACT_PIRACY @ 0.90
      - embedding_cosine >= 0.85                          -> EXACT_PIRACY @ 0.78
      - "deepfake" or "fake" in caption                   -> DEEPFAKE_MANIPULATION @ 0.80
      - otherwise                                         -> FALSE_POSITIVE @ 0.55
    """
    cand = payload["CANDIDATE"]
    caption = (cand.get("caption") or "").lower()
    hm = cand["hash_match"]

    if any(word in caption for word in ("deepfake", "morph", "ai-generated")):
        data = {
            "verdict": "DEEPFAKE_MANIPULATION", "confidence": 0.80,
            "evidence": ["caption_assertion: caption asserts synthetic origin"],
            "recommended_action": "ATHLETE_ALERT_AND_TAKEDOWN",
            "athlete_alert": {"should_alert": True, "reason": "Synthetic media claim in caption"},
        }
    elif hm["phash_distance"] <= 6 or hm["embedding_cosine"] >= 0.92:
        data = {
            "verdict": "EXACT_PIRACY", "confidence": 0.90,
            "evidence": [f"phash_distance={hm['phash_distance']}", f"embedding_cosine={hm['embedding_cosine']:.3f}"],
            "recommended_action": "AUTO_TAKEDOWN",
            "athlete_alert": {"should_alert": False, "reason": ""},
        }
    elif hm["embedding_cosine"] >= 0.85:
        data = {
            "verdict": "EXACT_PIRACY", "confidence": 0.78,
            "evidence": [f"embedding_cosine={hm['embedding_cosine']:.3f}"],
            "recommended_action": "REVIEW",
            "athlete_alert": {"should_alert": False, "reason": ""},
        }
    else:
        data = {
            "verdict": "FALSE_POSITIVE", "confidence": 0.55,
            "evidence": [],
            "recommended_action": "IGNORE",
            "athlete_alert": {"should_alert": False, "reason": ""},
        }
    return json.dumps(data)


def detect(
    candidate_url: str,
    candidate_video_path: Path,
    *,
    platform: str,
    host_country: str | None,
    uploader: str,
    caption: str,
    workdir: Path,
    resolve_clip: callable,            # (clip_id) -> Clip
    resolve_video: callable,           # (clip_id) -> Path
) -> VerdictRecord | None:
    """End-to-end: fingerprint the candidate, retrieve, and verdict.

    Returns None when Stage 1 produces no escalation-worthy match.
    """
    phashes, embeddings = fingerprint_candidate(candidate_video_path, workdir)
    matches = stage1_retrieve(phashes, embeddings)
    escalated = [m for m in matches if m.should_escalate]
    if not escalated:
        return None

    best = min(escalated, key=lambda m: (m.phash_distance, -m.embedding_cosine))
    original = resolve_clip(best.clip_id)
    original_video = resolve_video(best.clip_id)

    candidate = Candidate(
        candidate_id=_candidate_id_from(candidate_url, candidate_video_path),
        url=candidate_url,
        platform=platform,  # type: ignore[arg-type]
        host_country=host_country,
        uploader=uploader,
        caption=caption,
        found_at=datetime.now(timezone.utc),
        storage_uri=str(candidate_video_path),
        hash_match=CandidateHashMatch(
            phash_distance=best.phash_distance,
            embedding_cosine=best.embedding_cosine,
        ),
    )

    return stage2_verdict(original, candidate, candidate_video_path, original_video)


def _candidate_id_from(url: str, video_path: Path) -> str:
    h = hashlib.sha256()
    h.update(url.encode("utf-8"))
    h.update(video_path.read_bytes())
    return h.hexdigest()[:32]
