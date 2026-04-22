# Solution Brief — Aegis

**Track:** PS#1, Digital Asset Protection
**Challenge:** Google Solution Challenge 2026 · Build with AI
**Submission:** Phase 1 — 24 Apr 2026

---

## 1. One-paragraph summary

Aegis is an authenticity layer for sport. At publication, Aegis cryptographically signs official media with a C2PA content credential and a dual-layer fingerprint (perceptual hash plus Vertex AI multimodal embedding). In the wild, a two-stage detector — fast retrieval over Vertex AI Vector Search, semantic verification by Gemini 2.5 Pro — catches unauthorized reproductions even when they have been cropped, mirrored, re-encoded, upscaled, or overlaid with captions. A dedicated deepfake classifier detects AI-generated or manipulated athlete imagery and triggers a bilingual English/Hindi alert on an athlete-facing view. An agentic takedown pipeline drafts platform-specific notices jurisdiction-aware — DMCA §512(c) for US-hosted content, IT Rules 2021 for India-hosted content — files them, and anchors a tamper-evident daily Merkle receipt via Cloud KMS for public verification. The product is opt-in for athletes, ethics-first in its data posture, and is explicitly not DRM (see `docs/why-not-drm.md`).

## 2. Architecture

```
                                      ┌─────────────────────────┐
                                      │  Rights-holder dashboard │ (Firebase Auth)
                                      └─────────┬───────────────┘
                                                │
  ┌──────────────────┐   POST /ingest           ▼            ┌───────────────────────┐
  │  Upload official ├─►  Cloud Run API  ───►  Firestore ─►  │ Vertex AI             │
  │  clip (mp4)      │       │  │                            │  Multimodal embeddings │
  └──────────────────┘       │  │                            │  + Vector Search       │
                             │  ▼                            └───────────────────────┘
                             │  Cloud KMS  ───►  C2PA manifest (Cloud Storage)
                             │
                             │ Pub/Sub (async ops)
                             ▼
                       ┌───────────────────────┐
                       │  Cloud Run Jobs       │
                       │    crawler            │ ──► public URLs (robots.txt-aware)
                       │    matcher            │ ──► pHash + Vector Search
                       │    classifier         │ ──► Gemini 2.5 Pro verdict.txt
                       │    deepfake           │ ──► Gemini deepfake_verdict.txt
                       │    takedown agents    │ ──► mock platform endpoints
                       └───────────┬───────────┘
                                   │
                                   ▼
                 ┌──────────────────────────────┐
                 │  Athlete-facing view (EN/HI) │ ◄── default, unauthenticated landing
                 │  /verify page (public)       │ ◄── Merkle-anchored receipt lookup
                 └──────────────────────────────┘
```

Detailed architecture diagram: `docs/architecture.png` (to be exported from draw.io on final submission).

## 3. Key innovations (scoring highlights)

### Dual-layer fingerprinting solves scale *and* adversarial robustness
- **Perceptual hashing (pHash)** over 8 keyframes per clip gives fast near-exact recall.
- **Vertex AI multimodal embeddings** per keyframe, indexed in **Vertex AI Vector Search**, give semantic recall under heavy adversarial transforms.
- **Gemini 2.5 Pro** makes the final verdict call against `backend/prompts/verdict.txt` — a strictly-JSON-responding system prompt whose decision space spans `EXACT_PIRACY`, `EDITED_HIGHLIGHT`, `SCREEN_RECORDING`, `FAIR_USE_COMMENTARY`, `DEEPFAKE_MANIPULATION`, `FALSE_POSITIVE`.
- The prompt is version-controlled and is considered part of the novelty of the system (see §4).

### Deepfake detection as a first-class pillar, not a bolt-on
- Dedicated `backend/prompts/deepfake_verdict.txt` with an explicit cue taxonomy (temporal face flicker, blend seam, lip-sync drift, spectral flatness, prosody monotony, reverb mismatch, and more).
- Athlete-facing view is the default unauthenticated landing page, bilingual English/Hindi.
- Opt-in enrolment; no likeness dossier without explicit consent.

### Agentic takedown, jurisdiction-aware
- Per-platform drafting: the `backend/takedown.py` module routes detections to `prompts/takedown_us.txt` (DMCA §512(c)) or `prompts/takedown_in.txt` (IT Rules 2021 + MeitY November 2023 advisory) based on host country and platform.
- The IN template explicitly invokes Rule 3(2)(b) for artificially morphed images and the 24-hour timeline for synthetic media; the US template fully populates the six statutory elements of §512(c)(3).
- Submission in Phase 1 is to honeypot Cloud Run endpoints that return structured receipts — measuring *pipeline integrity* (our pipeline), not platform response rates (not ours to measure).

### Tamper-evident public audit
- Every provenance claim and every filed takedown is hashed into a daily Merkle root, signed via Cloud KMS.
- The public `/verify` endpoint returns the receipt for any detection ID — judges or auditors can independently verify any claim we make.
- This is the trust-layer differentiator against "another piracy dashboard."

## 4. The prompt *is* part of the system

`backend/prompts/verdict.txt` is version-controlled and is the single highest-leverage artefact in the repository. The prompt:

- Locks the verdict space to six labels, each with a concrete downstream action.
- Explicitly enumerates which adversarial transforms do *not* justify a FALSE_POSITIVE.
- Defines action routing (`AUTO_TAKEDOWN`, `REVIEW`, `IGNORE`, `ATHLETE_ALERT_AND_TAKEDOWN`) with published confidence thresholds so the system's behaviour is transparent.

Iterating this prompt is part of the team's Thursday work; the commit history on this file is expected to be visible evidence of the team's engineering rigor.

## 5. Tech stack

- **Models:** Gemini 2.5 Pro (Vertex AI) · Vertex AI Multimodal Embeddings (`multimodal-embedding-001`) · ImageHash (pHash)
- **Infra:** Cloud Run (API) · Cloud Run Jobs (crawler, matcher, classifier, takedown agents) · Vertex AI Vector Search (ScaNN) · Firestore · Cloud Storage · Cloud KMS · Pub/Sub · Firebase Hosting
- **Frontend:** React 18 · Vite · Tailwind · react-i18next (EN/HI)
- **Languages:** Python 3.11 (backend + benchmark) · TypeScript (frontend)
- **Auth:** Firebase Auth (rights-holder dashboard only; athlete view is public and opt-in)

## 6. Benchmarks (Phase-1 targets)

See [`docs/benchmarks.md`](benchmarks.md) for the full table. Headline targets:

- **Recall on single adversarial transforms at ≤ 5% FPR:** ≥ 85%
- **Precision@5 on Vector Search retrieval:** ≥ 0.80
- **End-to-end latency (detection → verdict → DMCA draft):** < 90 s p95
- **Deepfake detection accuracy (zero-shot Gemini):** ≥ 0.80 on a 30-clip labelled set
- **Pipeline integrity** (classified match → correctly-formatted, filed, logged notice): **100%**

The pipeline-integrity metric is deliberately defined as a property of *our* pipeline, not of platforms we do not control. See `docs/benchmarks.md` for why this framing is load-bearing.

## 7. Scalability plan

- **Index:** Vertex AI Vector Search (ScaNN) scales to billions of datapoints; Phase-1 uses 10K-item index, Finale-target is 100K.
- **Detection workers:** Cloud Run Jobs horizontal autoscale; Pub/Sub decouples crawler → matcher → classifier so each stage back-pressures independently.
- **Federated fingerprint index (Phase 2):** two synthetic "rights-holder" clients via Flower or TensorFlow Federated, gestured at in the roadmap slide only.
- **Cost floor:** Phase-1 demo runs within GCP free tier plus < ₹1000 of Gemini 2.5 Pro calls.

## 8. SDG alignment

- **Primary:** SDG 5 (Gender Equality), SDG 16 (Peace, Justice and Strong Institutions).
- **Secondary:** SDG 8 (Decent Work — athlete and creator livelihoods), SDG 9 (Innovation).

Rationale and enforcement in the submission: [`docs/sdg-alignment.md`](sdg-alignment.md). The primary-tier SDGs are visible on slide #3 of the deck, in the cold open of the demo video, and in the beneficiary ordering of the product UX.

## 9. Ethics

Full statement: [`docs/ethics.md`](ethics.md). Highlights: DFDC + Celeb-DF only for training data; no generation path in the product; opt-in athlete enrolment; takedown restraint below confidence thresholds; legally defensible crawling (public URLs, robots.txt-aware, no auth bypass); published failure modes.

## 10. Demo

3-minute demo storyboard: [`docs/demo-cold-open.md`](demo-cold-open.md) for the opening 30 seconds; [`aegis-build-plan.md`](../aegis-build-plan.md) §8 for the remainder, with the adjustments listed in the cold-open doc.

Flagship scenario: [`docs/case-study.md`](case-study.md) — "Test-Subject Meera," a deliberately fictional woman cricketer persona, with the `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark rule.

## 11. Repository map

```
aegis/
├── README.md                     (DRM-preempt top-fold)
├── aegis-build-plan.md           (48-hour sprint plan, unchanged)
├── backend/
│   ├── main.py                   (FastAPI on Cloud Run)
│   ├── ingest.py                 (C2PA sign + keyframes + fingerprint)
│   ├── detect.py                 (two-stage: pHash + Vector Search + Gemini)
│   ├── takedown.py               (jurisdiction router + notice filing)
│   ├── schema.py                 (Pydantic + Firestore models)
│   ├── vector_index.py           (Vertex Vector Search with LOCAL fallback)
│   ├── storage.py                (Firestore with LOCAL fallback)
│   ├── prompts/
│   │   ├── verdict.txt           (Gemini verdict system prompt)
│   │   ├── deepfake_verdict.txt  (likeness-abuse classifier prompt)
│   │   ├── takedown_us.txt       (DMCA §512(c) template)
│   │   └── takedown_in.txt       (IT Rules 2021 template)
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                     (React + Vite + Tailwind, EN/HI)
├── benchmark/
│   └── generate_variants.py      (seeded adversarial variant generator)
├── data/
│   ├── originals/                (30 CC-licensed clips)
│   ├── adversarial/              (generated variants)
│   └── case-study/               (Test-Subject Meera sources + logs)
└── docs/
    ├── problem_statement.md      (this doc's sibling)
    ├── solution_brief.md         (this file)
    ├── why-not-drm.md
    ├── sdg-alignment.md
    ├── ethics.md
    ├── case-study.md
    ├── demo-cold-open.md
    └── benchmarks.md
```
