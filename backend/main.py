"""FastAPI app. Routes:

  POST /ingest       — rights-holder uploads official clip; we sign + fingerprint + index
  POST /detect       — crawler-worker posts a candidate URL; we run two-stage detection
  POST /takedown     — draft (and optionally file) a notice from an existing verdict
  POST /athlete/enroll — opt-in athlete enrolment
  GET  /verify/{id}  — public verification endpoint for a Merkle-anchored receipt
  GET  /healthz      — liveness

Firestore-backed. Vertex AI for embeddings + Gemini. Honeypot mocks for takedown endpoints.

Production wiring (GCP creds, Firestore client, Vector Search index) reads from env:
  VERTEX_AI_PROJECT, VERTEX_AI_LOCATION, VERTEX_VECTOR_INDEX_ID, VERTEX_VECTOR_ENDPOINT_ID,
  VERTEX_VECTOR_DEPLOYED_INDEX_ID, GOOGLE_APPLICATION_CREDENTIALS, AEGIS_INDEX_MODE.
"""

from __future__ import annotations

import asyncio
import os
import tempfile
import threading
from datetime import datetime, timezone
from pathlib import Path
from uuid import uuid4

from fastapi import FastAPI, File, Form, HTTPException, UploadFile
from fastapi.middleware.cors import CORSMiddleware
from pydantic import BaseModel

from backend import detect as detect_mod
from backend import ingest as ingest_mod
from backend import takedown as takedown_mod
from backend import vector_index
from backend.provenance import merkle as merkle_mod
from backend.schema import (
    AthleteEnrollment,
    Candidate,
    Clip,
    MerkleReceipt,
    RightsHolderContact,
    VerdictRecord,
)
from backend.storage import AegisStore

app = FastAPI(title="Aegis", version="0.1.0")

app.add_middleware(
    CORSMiddleware,
    allow_origins=os.environ.get("ALLOWED_ORIGINS", "*").split(","),
    allow_methods=["*"],
    allow_headers=["*"],
)

store = AegisStore()

WORKDIR = Path(os.environ.get("AEGIS_WORKDIR", tempfile.gettempdir())) / "aegis"
WORKDIR.mkdir(parents=True, exist_ok=True)


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "index_mode": os.environ.get("AEGIS_INDEX_MODE", "LOCAL")}


@app.get("/demo/status")
def demo_status() -> dict:
    """Which backends is this process actually talking to? Use to confirm the
    API is in GCP mode (not LOCAL) before recording the demo video."""
    def present(key: str) -> bool:
        return bool(os.environ.get(key))

    return {
        "index_mode":     os.environ.get("AEGIS_INDEX_MODE", "LOCAL"),
        "storage_mode":   os.environ.get("AEGIS_STORAGE_MODE", "LOCAL"),
        "kms_mode":       os.environ.get("AEGIS_KMS_MODE", "LOCAL"),
        "anchor_mode":    os.environ.get("AEGIS_ANCHOR_MODE", "EAGER"),
        "demo_mode":      os.environ.get("AEGIS_DEMO_MODE", "").lower() in ("1", "true", "yes"),
        "gemini_live":    present("GOOGLE_API_KEY") or present("VERTEX_AI_PROJECT"),
        "vector_search_configured": present("VERTEX_VECTOR_INDEX_ID"),
        "mock_endpoints": {
            "x":        present("MOCK_X_ENDPOINT"),
            "youtube":  present("MOCK_YOUTUBE_ENDPOINT"),
            "meta":     present("MOCK_META_ENDPOINT"),
            "telegram": present("MOCK_TELEGRAM_ENDPOINT"),
        },
    }


# ---------- /ingest ----------

class IngestResponse(BaseModel):
    clip_id: str
    c2pa_manifest_url: str


@app.post("/ingest", response_model=IngestResponse)
async def ingest_route(
    video: UploadFile = File(...),
    title: str = Form(...),
    sport: str = Form(...),
    event: str = Form(...),
    rights_holder: str = Form(...),
    rights_holder_name: str = Form(...),
    rights_holder_title: str = Form(...),
    rights_holder_address: str = Form(...),
    rights_holder_phone: str = Form(...),
    rights_holder_email: str = Form(...),
    athletes_csv: str = Form(""),
) -> IngestResponse:
    if not video.filename:
        raise HTTPException(400, "missing filename")

    video_path = WORKDIR / f"upload_{uuid4().hex}_{video.filename}"
    video_path.write_bytes(await video.read())

    contact = RightsHolderContact(
        name=rights_holder_name,
        title=rights_holder_title,
        address=rights_holder_address,
        phone=rights_holder_phone,
        email=rights_holder_email,
    )
    athletes = [a.strip() for a in athletes_csv.split(",") if a.strip()]

    clip, embeddings = ingest_mod.ingest(
        video_path,
        title=title, sport=sport, event=event,
        rights_holder=rights_holder, rights_holder_contact=contact,
        athletes=athletes, workdir=WORKDIR,
    )

    vector_index.upsert_clip(clip.clip_id, embeddings, clip.phash_per_frame)

    store.put_clip(clip)
    store.register_clip_video(clip.clip_id, video_path)

    # Anchor this clip into the current-day Merkle log.
    _anchor_leaf(merkle_mod.build_leaf_for_clip(clip.clip_id, clip.model_dump(mode="json")))

    return IngestResponse(clip_id=clip.clip_id, c2pa_manifest_url=str(clip.c2pa_manifest_url))


# ---------- /detect ----------

class DetectRequest(BaseModel):
    candidate_url: str
    platform: str
    host_country: str | None = None
    uploader: str
    caption: str = ""


@app.post("/detect")
async def detect_route(
    video: UploadFile = File(...),
    candidate_url: str = Form(...),
    platform: str = Form(...),
    uploader: str = Form(...),
    caption: str = Form(""),
    host_country: str | None = Form(None),
) -> dict:
    video_path = WORKDIR / f"candidate_{uuid4().hex}_{video.filename}"
    video_path.write_bytes(await video.read())

    result = detect_mod.detect(
        candidate_url=candidate_url,
        candidate_video_path=video_path,
        platform=platform,
        host_country=host_country,
        uploader=uploader,
        caption=caption,
        workdir=WORKDIR / "detect" / uuid4().hex,
        resolve_clip=store.get_clip,
        resolve_video=store.get_clip_video,
    )
    if result is None:
        return {"matched": False}

    verdict, candidate = result
    # Persist the Candidate first — /takedown looks it up by id. Without this,
    # the takedown path 404s. (Audit v2 ship-blocker.)
    store.put_candidate(candidate)
    store.put_verdict(verdict)
    _anchor_leaf(merkle_mod.build_leaf_for_verdict(verdict.detection_id, verdict.model_dump(mode="json")))
    return {"matched": True, "verdict": verdict.model_dump()}


# ---------- /takedown ----------

class TakedownRequest(BaseModel):
    detection_id: str
    file_now: bool = True


@app.post("/takedown")
def takedown_route(req: TakedownRequest) -> dict:
    verdict = store.get_verdict(req.detection_id)
    if verdict is None:
        raise HTTPException(404, "detection_id not found")

    original = store.get_clip(verdict.original_clip_id)
    candidate = store.get_candidate(verdict.candidate_id)
    if original is None or candidate is None:
        raise HTTPException(404, "clip or candidate not found for detection")

    try:
        notice = takedown_mod.draft_notice(verdict, original, candidate)
    except takedown_mod.BelowThreshold as e:
        raise HTTPException(409, str(e))

    if req.file_now:
        notice = takedown_mod.file_notice(notice)
    store.put_takedown(notice)
    _anchor_leaf(merkle_mod.build_leaf_for_notice(notice.notice_id, notice.model_dump(mode="json")))
    return {"notice": notice.model_dump()}


# ---------- /athlete/enroll ----------

class EnrollRequest(BaseModel):
    display_name: str
    preferred_language: str = "en-hi"


@app.post("/athlete/enroll")
def enroll_route(req: EnrollRequest) -> dict:
    enrollment = AthleteEnrollment(
        athlete_id=str(uuid4()),
        display_name=req.display_name,
        preferred_language=req.preferred_language,  # type: ignore[arg-type]
        enrolled_at=datetime.now(timezone.utc),
    )
    store.put_athlete(enrollment)
    return {"athlete_id": enrollment.athlete_id}


# ---------- /verify ----------

@app.get("/verify/{detection_id}")
def verify_route(detection_id: str) -> dict:
    verdict = store.get_verdict(detection_id)
    if verdict is None:
        raise HTTPException(404, "detection_id not found")
    receipt = store.get_merkle_receipt_for(detection_id)
    return {
        "detection_id":    detection_id,
        "verdict":         verdict.verdict.value,
        "confidence":      verdict.confidence,
        "merkle_receipt":  receipt.model_dump() if receipt else None,
    }


@app.post("/provenance/anchor")
def anchor_route() -> dict:
    """Close out the current batch of pending leaves into a Merkle receipt.

    Called on a schedule in production (Cloud Scheduler → Cloud Run Jobs, daily).
    Exposed as an HTTP endpoint so the demo can trigger it on-demand.
    """
    return _flush_pending_leaves()


# ---------- Merkle batch buffer ----------
#
# Under FastAPI's thread-pool for sync handlers, appends + drains can race. A
# plain threading.Lock is sufficient — we do not touch _PENDING from async
# coroutines. If _anchor_leaf ever becomes awaitable, swap in an asyncio.Lock.

_PENDING: list[merkle_mod.Leaf] = []
_PENDING_LOCK = threading.Lock()


def _anchor_leaf(leaf: merkle_mod.Leaf) -> None:
    with _PENDING_LOCK:
        _PENDING.append(leaf)
    # Phase-1 demo reality: we flush after every leaf so /verify returns a receipt
    # immediately. In production, swap for a scheduled daily flush + a /verify that
    # tolerates unanchored detections with a clearly-marked "pending anchor" state.
    if os.environ.get("AEGIS_ANCHOR_MODE", "EAGER") == "EAGER":
        _flush_pending_leaves()


def _flush_pending_leaves() -> dict:
    with _PENDING_LOCK:
        if not _PENDING:
            return {"flushed": 0}
        batch = list(_PENDING)
        _PENDING.clear()
    # Outside the lock: anchor + persist. Losing the lock early lets concurrent
    # ingest/detect handlers queue new leaves while we sign the batch.
    receipt_dict = merkle_mod.anchor_batch(batch)
    receipt = MerkleReceipt(**receipt_dict)
    store.put_merkle_receipt(receipt, detection_ids=[l.id for l in batch])
    return {"flushed": len(batch), "receipt": receipt.model_dump()}
