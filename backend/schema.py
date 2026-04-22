from __future__ import annotations

from datetime import datetime
from enum import Enum
from typing import Literal

from pydantic import BaseModel, Field, HttpUrl


class Verdict(str, Enum):
    EXACT_PIRACY = "EXACT_PIRACY"
    EDITED_HIGHLIGHT = "EDITED_HIGHLIGHT"
    SCREEN_RECORDING = "SCREEN_RECORDING"
    FAIR_USE_COMMENTARY = "FAIR_USE_COMMENTARY"
    DEEPFAKE_MANIPULATION = "DEEPFAKE_MANIPULATION"
    FALSE_POSITIVE = "FALSE_POSITIVE"


class Action(str, Enum):
    AUTO_TAKEDOWN = "AUTO_TAKEDOWN"
    ATHLETE_ALERT_AND_TAKEDOWN = "ATHLETE_ALERT_AND_TAKEDOWN"
    REVIEW = "REVIEW"
    IGNORE = "IGNORE"


class Jurisdiction(str, Enum):
    IN = "IN"
    US = "US"
    OTHER = "OTHER"


class RightsHolderContact(BaseModel):
    name: str
    title: str
    address: str
    phone: str
    email: str


class Clip(BaseModel):
    """A signed, rights-holder-published original clip."""

    clip_id: str
    title: str
    sport: str
    event: str
    first_published: datetime
    rights_holder: str
    rights_holder_contact: RightsHolderContact
    athletes: list[str] = Field(default_factory=list)
    c2pa_manifest_url: HttpUrl
    storage_uri: str
    phash_per_frame: list[str]
    embedding_index_id: str


class CandidateHashMatch(BaseModel):
    phash_distance: int
    embedding_cosine: float


class Candidate(BaseModel):
    """A suspect clip discovered on a public platform."""

    candidate_id: str
    url: HttpUrl
    platform: Literal["x", "youtube", "meta", "telegram", "mock", "other"]
    host_country: str | None = None
    uploader: str
    caption: str = ""
    found_at: datetime
    storage_uri: str
    hash_match: CandidateHashMatch


class VerdictEvidence(BaseModel):
    cue: str
    notes: str | None = None


class AthleteAlert(BaseModel):
    should_alert: bool = False
    reason: str = ""


class VerdictRecord(BaseModel):
    """Output of Gemini verdict agent, persisted to Firestore."""

    detection_id: str
    original_clip_id: str
    candidate_id: str
    verdict: Verdict
    confidence: float = Field(ge=0.0, le=1.0)
    evidence: list[str]
    recommended_action: Action
    athlete_alert: AthleteAlert = Field(default_factory=AthleteAlert)
    created_at: datetime

    def should_auto_takedown(self) -> bool:
        return self.recommended_action in (
            Action.AUTO_TAKEDOWN,
            Action.ATHLETE_ALERT_AND_TAKEDOWN,
        )


class TakedownNotice(BaseModel):
    """A drafted, filed takedown notice; one notice per infringing URL."""

    notice_id: str
    detection_id: str
    jurisdiction: Jurisdiction
    target_url: HttpUrl
    platform: str
    subject: str
    body: str
    drafted_at: datetime
    filed_at: datetime | None = None
    filed_to_endpoint: str | None = None
    platform_ticket_id: str | None = None
    status: Literal["DRAFT", "FILED", "ACKNOWLEDGED", "RESOLVED", "REJECTED"] = "DRAFT"


class MerkleReceipt(BaseModel):
    """One daily Merkle anchor, Cloud-KMS-signed, published on /verify."""

    receipt_id: str
    date: str  # YYYY-MM-DD
    merkle_root_hex: str
    kms_key_version: str
    kms_signature_b64: str
    leaf_count: int
    first_leaf_id: str
    last_leaf_id: str


class AthleteEnrollment(BaseModel):
    """Opt-in record; no dossier exists without this."""

    athlete_id: str
    display_name: str
    preferred_language: Literal["en", "hi", "en-hi"]
    likeness_embedding_id: str | None = None
    enrolled_at: datetime
    revoked_at: datetime | None = None

    @property
    def is_active(self) -> bool:
        return self.revoked_at is None


FIRESTORE_COLLECTIONS: dict[str, type[BaseModel]] = {
    "clips": Clip,
    "candidates": Candidate,
    "verdicts": VerdictRecord,
    "takedowns": TakedownNotice,
    "receipts": MerkleReceipt,
    "athletes": AthleteEnrollment,
}
