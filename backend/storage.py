"""Storage layer.

Two backends:
  - LOCAL: in-memory + local filesystem for 48h-sprint integration runs.
  - GCP:   Firestore + Cloud Storage for submission.

Select with `AEGIS_STORAGE_MODE={LOCAL,GCP}` (default LOCAL).
"""

from __future__ import annotations

import os
import threading
from pathlib import Path

from backend.schema import (
    AthleteEnrollment,
    Candidate,
    Clip,
    MerkleReceipt,
    TakedownNotice,
    VerdictRecord,
)


def _mode() -> str:
    return os.environ.get("AEGIS_STORAGE_MODE", "LOCAL")


class AegisStore:
    def __init__(self) -> None:
        self._lock = threading.Lock()
        self._clips: dict[str, Clip] = {}
        self._clip_videos: dict[str, Path] = {}
        self._candidates: dict[str, Candidate] = {}
        self._verdicts: dict[str, VerdictRecord] = {}
        self._takedowns: dict[str, TakedownNotice] = {}
        self._athletes: dict[str, AthleteEnrollment] = {}
        self._receipts_by_detection: dict[str, MerkleReceipt] = {}

        if _mode() == "GCP":
            from google.cloud import firestore
            self._fs = firestore.Client()
        else:
            self._fs = None

    # ---- Clips
    def put_clip(self, clip: Clip) -> None:
        with self._lock:
            self._clips[clip.clip_id] = clip
        if self._fs:
            self._fs.collection("clips").document(clip.clip_id).set(clip.model_dump(mode="json"))

    def get_clip(self, clip_id: str) -> Clip | None:
        with self._lock:
            cached = self._clips.get(clip_id)
        if cached is not None:
            return cached
        if self._fs:
            doc = self._fs.collection("clips").document(clip_id).get()
            if doc.exists:
                return Clip.model_validate(doc.to_dict())
        return None

    def register_clip_video(self, clip_id: str, path: Path) -> None:
        with self._lock:
            self._clip_videos[clip_id] = path

    def get_clip_video(self, clip_id: str) -> Path | None:
        """Return the on-disk path of the original video for a clip, or None.

        In-memory video registry is process-local; Firestore does not persist
        it. Callers (notably backend.detect) must tolerate None and skip the
        Stage-2 Gemini pair-verdict when the original bytes are unavailable.
        """
        with self._lock:
            return self._clip_videos.get(clip_id)

    # ---- Candidates
    def put_candidate(self, candidate: Candidate) -> None:
        with self._lock:
            self._candidates[candidate.candidate_id] = candidate
        if self._fs:
            self._fs.collection("candidates").document(candidate.candidate_id).set(
                candidate.model_dump(mode="json")
            )

    def get_candidate(self, candidate_id: str) -> Candidate | None:
        with self._lock:
            cached = self._candidates.get(candidate_id)
        if cached is not None:
            return cached
        if self._fs:
            doc = self._fs.collection("candidates").document(candidate_id).get()
            if doc.exists:
                return Candidate.model_validate(doc.to_dict())
        return None

    # ---- Verdicts
    def put_verdict(self, verdict: VerdictRecord) -> None:
        with self._lock:
            self._verdicts[verdict.detection_id] = verdict
        if self._fs:
            self._fs.collection("verdicts").document(verdict.detection_id).set(
                verdict.model_dump(mode="json")
            )

    def get_verdict(self, detection_id: str) -> VerdictRecord | None:
        with self._lock:
            cached = self._verdicts.get(detection_id)
        if cached is not None:
            return cached
        if self._fs:
            doc = self._fs.collection("verdicts").document(detection_id).get()
            if doc.exists:
                return VerdictRecord.model_validate(doc.to_dict())
        return None

    # ---- Takedowns
    def put_takedown(self, notice: TakedownNotice) -> None:
        with self._lock:
            self._takedowns[notice.notice_id] = notice
        if self._fs:
            self._fs.collection("takedowns").document(notice.notice_id).set(
                notice.model_dump(mode="json")
            )

    # ---- Athletes
    def put_athlete(self, enrollment: AthleteEnrollment) -> None:
        with self._lock:
            self._athletes[enrollment.athlete_id] = enrollment
        if self._fs:
            self._fs.collection("athletes").document(enrollment.athlete_id).set(
                enrollment.model_dump(mode="json")
            )

    # ---- Receipts
    def put_merkle_receipt(self, receipt: MerkleReceipt, detection_ids: list[str]) -> None:
        with self._lock:
            for d in detection_ids:
                self._receipts_by_detection[d] = receipt
        if self._fs:
            self._fs.collection("receipts").document(receipt.receipt_id).set(
                receipt.model_dump(mode="json")
            )

    def get_merkle_receipt_for(self, detection_id: str) -> MerkleReceipt | None:
        with self._lock:
            return self._receipts_by_detection.get(detection_id)
