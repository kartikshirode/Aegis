"""Honeypot platform endpoint — runs one per platform (X, YouTube, Meta, Telegram).

Usage — four Cloud Run services, each with a different PLATFORM env:
    PLATFORM=x          uvicorn services.mock_platforms.app:app --port 8101
    PLATFORM=youtube    uvicorn services.mock_platforms.app:app --port 8102
    PLATFORM=meta       uvicorn services.mock_platforms.app:app --port 8103
    PLATFORM=telegram   uvicorn services.mock_platforms.app:app --port 8104

Each returns a structured receipt that matches the shape the real platform would.
Ticket IDs are deterministic per-(platform, notice_id) so the integration test is
idempotent across runs.

This module is a benchmark harness. It is never a real platform. Every notice
submitted here is stored in-memory only and discarded on restart.
"""

from __future__ import annotations

import hashlib
import os
import time
from typing import Literal

from fastapi import FastAPI
from pydantic import BaseModel

PLATFORM = os.environ.get("PLATFORM", "mock").lower()

app = FastAPI(title=f"Aegis Mock — {PLATFORM}", version="0.1.0")


class NoticeIn(BaseModel):
    notice_id: str
    detection_id: str
    jurisdiction: Literal["IN", "US", "OTHER"]
    target_url: str
    subject: str
    body: str


class NoticeOut(BaseModel):
    ticket_id: str
    platform: str
    received_at: float
    expected_decision_by: float
    echo_jurisdiction: str


_RECEIVED: dict[str, NoticeOut] = {}


@app.get("/healthz")
def healthz() -> dict:
    return {"ok": True, "platform": PLATFORM, "received": len(_RECEIVED)}


@app.post("/takedown", response_model=NoticeOut)
def takedown(notice: NoticeIn) -> NoticeOut:
    # Shape per platform — rough approximations of real receipt shapes.
    now = time.time()
    sla_seconds = {
        "x":        24 * 3600,
        "youtube":  72 * 3600,
        "meta":     48 * 3600,
        "telegram": 72 * 3600,
    }.get(PLATFORM, 72 * 3600)

    # IT Rules 2021 + MeitY Nov 2023: 24h for synthetic / morphed content.
    body_lower = notice.body.lower()
    is_synthetic_signal = (
        "synthetic" in body_lower
        or "morphed" in body_lower
        or "Rule 3(2)(b)" in notice.body
    )
    if notice.jurisdiction == "IN" and is_synthetic_signal:
        sla_seconds = 24 * 3600

    ticket_id = _deterministic_ticket(PLATFORM, notice.notice_id)
    receipt = NoticeOut(
        ticket_id=ticket_id,
        platform=PLATFORM,
        received_at=now,
        expected_decision_by=now + sla_seconds,
        echo_jurisdiction=notice.jurisdiction,
    )
    _RECEIVED[notice.notice_id] = receipt
    return receipt


@app.get("/takedown/{notice_id}")
def lookup(notice_id: str) -> NoticeOut:
    return _RECEIVED[notice_id]


def _deterministic_ticket(platform: str, notice_id: str) -> str:
    h = hashlib.sha256(f"{platform}:{notice_id}".encode("utf-8")).hexdigest()
    return f"{platform.upper()}-{h[:12].upper()}"
