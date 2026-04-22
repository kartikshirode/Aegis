"""Takedown drafting + filing.

Given a VerdictRecord above threshold, pick the jurisdiction, load the matching
prompt template, call Gemini to produce a copy-paste-ready notice, and submit
to the configured endpoint for the candidate's platform.

The endpoints are mock honeypots for the Phase-1 demo (see README 'mock endpoints').
Real platform submission is a Phase-2 concern and is deliberately not wired up.
"""

from __future__ import annotations

import json
import os
import uuid
from datetime import datetime, timezone
from pathlib import Path

import httpx

from backend.schema import (
    Action,
    Candidate,
    Clip,
    Jurisdiction,
    TakedownNotice,
    Verdict,
    VerdictRecord,
)

PROMPTS_DIR = Path(__file__).parent / "prompts"


class BelowThreshold(Exception):
    """Raised when the verdict's recommended action does not permit auto-filing."""


def pick_jurisdiction(candidate: Candidate) -> Jurisdiction:
    """Delegate to the platform agent. Each agent already handles host_country."""
    from services.agents import get as get_agent
    return get_agent(candidate.platform).pick_jurisdiction(candidate)


def draft_notice(
    verdict_record: VerdictRecord,
    original: Clip,
    candidate: Candidate,
    *,
    affected_person: dict | None = None,
) -> TakedownNotice:
    """Build a notice by loading the jurisdiction-specific template and filling slots via Gemini."""
    if verdict_record.recommended_action not in (
        Action.AUTO_TAKEDOWN,
        Action.ATHLETE_ALERT_AND_TAKEDOWN,
    ):
        raise BelowThreshold(
            f"recommended_action={verdict_record.recommended_action.value} is not takedown-eligible"
        )

    jurisdiction = pick_jurisdiction(candidate)
    template_file = {
        Jurisdiction.IN: "takedown_in.txt",
        Jurisdiction.US: "takedown_us.txt",
        Jurisdiction.OTHER: "takedown_us.txt",  # DMCA template is the closest safe default
    }[jurisdiction]

    template = (PROMPTS_DIR / template_file).read_text(encoding="utf-8")

    detection_record = {
        "detection_id": verdict_record.detection_id,
        "verdict":      verdict_record.verdict.value,
        "confidence":   verdict_record.confidence,
        "original": {
            "title":             original.title,
            "rights_holder":     original.rights_holder,
            "rights_holder_contact": original.rights_holder_contact.model_dump(),
            "first_published":   original.first_published.isoformat(),
            "registration_num":  None,
            "c2pa_manifest_url": str(original.c2pa_manifest_url),
        },
        "candidate": {
            "url":          str(candidate.url),
            "platform":     candidate.platform,
            "uploaded_at":  None,
            "uploader":     candidate.uploader,
            "host_provider": _host_provider_of(candidate.platform),
            "host_provider_designated_agent_email": _dmca_agent_email(candidate.platform),
        },
        "evidence":     verdict_record.evidence,
    }

    if jurisdiction == Jurisdiction.IN:
        detection_record["affected_person"] = affected_person or {
            "name": "[athlete name — not enrolled]",
            "is_athlete_enrolled": False,
            "consent_to_file": False,
        }
        detection_record["rule_basis"] = _rule_basis_for_verdict(verdict_record, candidate.platform)

    raw = _call_gemini_for_draft(template, detection_record)
    subject, body = _split_subject_body(raw)

    return TakedownNotice(
        notice_id=str(uuid.uuid4()),
        detection_id=verdict_record.detection_id,
        jurisdiction=jurisdiction,
        target_url=candidate.url,
        platform=candidate.platform,
        subject=subject,
        body=body,
        drafted_at=datetime.now(timezone.utc),
        status="DRAFT",
    )


def file_notice(notice: TakedownNotice, *, endpoint: str | None = None) -> TakedownNotice:
    """Submit the notice to the configured endpoint and persist the receipt.

    The endpoint is a mock honeypot for Phase-1 demos. It is expected to return
    {"ticket_id": "..."} on success. Any non-2xx response marks the notice REJECTED.
    """
    target = endpoint or _resolve_mock_endpoint(notice.platform)
    if target is None:
        return notice

    try:
        resp = httpx.post(
            target,
            json={
                "notice_id":     notice.notice_id,
                "detection_id": notice.detection_id,
                "jurisdiction": notice.jurisdiction.value,
                "target_url":   str(notice.target_url),
                "subject":      notice.subject,
                "body":         notice.body,
            },
            timeout=10.0,
        )
        resp.raise_for_status()
        data = resp.json()
    except (httpx.HTTPError, ValueError):
        # ValueError catches a 200-OK response whose body isn't JSON — e.g. a
        # Cloudflare HTML block page. Without this, the notice leaks out as an
        # unhandled exception and is never persisted in REJECTED state.
        notice.status = "REJECTED"
        notice.filed_at = datetime.now(timezone.utc)
        notice.filed_to_endpoint = target
        return notice

    notice.status = "FILED"
    notice.filed_at = datetime.now(timezone.utc)
    notice.filed_to_endpoint = target
    notice.platform_ticket_id = data.get("ticket_id")
    return notice


def _rule_basis_for_verdict(verdict_record: VerdictRecord, platform: str) -> list[str]:
    """Platform agent owns the mapping."""
    from services.agents import get as get_agent
    return get_agent(platform).rule_basis_for(verdict_record)


def _host_provider_of(platform: str) -> str:
    from services.agents import get as get_agent
    return get_agent(platform).host_provider()


def _dmca_agent_email(platform: str) -> str:
    from services.agents import get as get_agent
    return get_agent(platform).designated_agent_email()


def _resolve_mock_endpoint(platform: str) -> str | None:
    from services.agents import get as get_agent
    return get_agent(platform).resolve_submit_endpoint()


def _call_gemini_for_draft(template: str, detection_record: dict) -> str:
    """Run the template against Gemini 2.5 Pro. Local-mock when no key is present."""
    if not os.environ.get("GOOGLE_API_KEY") and not os.environ.get("VERTEX_AI_PROJECT"):
        return _mock_draft(template, detection_record)

    from vertexai.generative_models import GenerativeModel

    model = GenerativeModel("gemini-2.5-pro", system_instruction=template)
    resp = model.generate_content(json.dumps(detection_record))
    return resp.text


def _mock_draft(template: str, rec: dict) -> str:
    """Produce a template-correct, deterministic draft for local dev / demo fallback.

    This is *not* a substitute for Gemini in submission. It exists so the
    pipeline is end-to-end testable without a live API key.
    """
    orig = rec["original"]
    cand = rec["candidate"]
    today = datetime.now(timezone.utc).date().isoformat()
    is_india = "IT Rules 2021" in template

    evidence_lines = "\n".join(f"  - {e}" for e in rec.get("evidence", [])) or "  - (see detection record)"

    if is_india:
        subject = f"Notice under IT Rules 2021 and IT Act Section 79 — Request for takedown — Reference {rec['detection_id']}"
        body = (
            f"To: {cand['host_provider_designated_agent_email'] or '[Grievance Officer]'}\n"
            f"From: {orig['rights_holder_contact']['name']}, {orig['rights_holder_contact']['title']}, on behalf of {orig['rights_holder']}\n"
            f"Date: {today}\n\n"
            f"Respected Grievance Officer,\n\n"
            f"This is a notice under the Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021, read with Section 79 of the Information Technology Act, 2000.\n\n"
            f"1. Impugned content: {cand['url']} on {cand['platform']}, uploaded by {cand['uploader']}.\n"
            f"2. Aegis detection reference: {rec['detection_id']} (classification: {rec['verdict']}, confidence {rec['confidence']}).\n"
            f"3. Evidence:\n{evidence_lines}\n"
            f"4. Legal basis: {', '.join(rec.get('rule_basis', ['copyright']))}.\n"
            f"5. Request: disable access within the timeline prescribed under the IT Rules 2021.\n"
            f"6. The original is authenticated via C2PA manifest at {orig['c2pa_manifest_url']}.\n\n"
            f"Yours faithfully,\n{orig['rights_holder_contact']['name']}\n{today}\n"
            f"[Electronic signature of record on file — signed via Aegis detection {rec['detection_id']}]\n"
        )
    else:
        subject = f"DMCA Section 512(c)(3) Notice of Claimed Infringement — {orig['title']}"
        body = (
            f"To: {cand['host_provider_designated_agent_email'] or '[designated agent]'}\n"
            f"From: {orig['rights_holder_contact']['name']}, {orig['rights_holder_contact']['title']}, on behalf of {orig['rights_holder']}\n"
            f"Date: {today}\n\n"
            f"Dear DMCA Designated Agent,\n\n"
            f"I am writing to provide notice of claimed infringement under 17 U.S.C. Section 512(c)(3), on behalf of {orig['rights_holder']}.\n\n"
            f"1. Copyrighted work: {orig['title']}, first published {orig['first_published']}. C2PA manifest: {orig['c2pa_manifest_url']}.\n"
            f"2. Infringing material: {cand['url']} on {cand['platform']}, uploader {cand['uploader']}. Detection {rec['detection_id']} (classification {rec['verdict']}, confidence {rec['confidence']}).\n"
            f"3. Evidence:\n{evidence_lines}\n"
            f"4. Good faith: I have a good faith belief that use of the material is not authorised.\n"
            f"5. Under penalty of perjury: I state that the information is accurate and that I am authorised to act.\n\n"
            f"Signature:\n{orig['rights_holder_contact']['name']}\n{today}\n"
            f"[Electronic signature of record on file — signed via Aegis detection {rec['detection_id']}]\n"
        )

    return f"{subject}\n\n{body}"


def _split_subject_body(raw: str) -> tuple[str, str]:
    head, _, body = raw.strip().partition("\n\n")
    subject = head.replace("Subject:", "", 1).strip() if head.lower().startswith("subject:") else head.strip()
    return subject, body.strip()
