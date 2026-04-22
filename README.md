# Aegis

**Authenticity for sport — built for athletes and fans, not the leagues.**

Aegis is a cryptographic-provenance + deepfake-defense + agentic-takedown platform for sports media. It is designed as an opt-in tool for athletes whose likenesses are targets of non-consensual synthetic media, and for rights-holders who want an audit-verifiable trail for their takedown operations. **It is not DRM** — see [docs/why-not-drm.md](docs/why-not-drm.md) before anything else.

Built for the **Google Solution Challenge 2026 — Build with AI** under PS#1 ("Protecting the Integrity of Digital Sports Media").

---

## The 30-second version

1. A rights-holder publishes an official clip. Aegis signs it with a **C2PA** content credential (Cloud KMS-backed) and fingerprints it two ways — perceptual hash plus Vertex AI multimodal embedding indexed in Vertex AI Vector Search.
2. Aegis's crawler discovers unauthorized re-uploads in the wild. A two-stage detector — fast retrieval, then **Gemini 2.5 Pro** semantic verdict against a version-controlled 6-label prompt — classifies each match. One of those labels is `DEEPFAKE_MANIPULATION`.
3. When the verdict is `DEEPFAKE_MANIPULATION` (or the athlete-likeness evidence in the verdict is strong), a bilingual **English + Hindi** alert lands on the athlete-facing view, which is the default unauthenticated landing page. **Phase 1 uses Gemini zero-shot multimodal classification as the deepfake signal; a fine-tuned classifier head is Phase-2 work.** The pipeline and the UX are fully wired; the classifier quality is what the benchmark measures and reports honestly.
4. An **agentic takedown pipeline** drafts platform-specific notices — **DMCA §512(c)** for US-hosted content, **IT Rules 2021 + MeitY Nov 2023 advisory** for India-hosted content — files them to per-platform endpoints, and tracks outcomes.
5. Every claim and every takedown is hashed into a daily **Merkle root** signed via Cloud KMS. Anyone can verify a receipt at `/verify/{detection_id}`.

## Why this is not DRM

DRM restricts *who can play* content. Aegis attests *what content is real*, is opt-in for the athlete, and is useless against paying consumers. The primary beneficiaries are athletes and fans; rights-holders benefit but are not the protagonists. Read the full treatment — including the India IT Rules 2021 / US DMCA §512(c) jurisdictional posture, the licensing stance (Apache-2.0 core), and the contrast table against DRM and Content Credentials — in [docs/why-not-drm.md](docs/why-not-drm.md).

## SDG framing

- **Primary:** SDG 5 (Gender Equality) · SDG 16 (Peace, Justice, and Strong Institutions).
- **Secondary:** SDG 8 (Decent Work — athlete and creator livelihoods) · SDG 9 (Innovation).

Full alignment + what is deliberately *not* claimed: [docs/sdg-alignment.md](docs/sdg-alignment.md).

## Repository map

```
.
├── aegis-build-plan.md            — 48-hour sprint plan (Apr 22 → Apr 24, 2026)
├── backend/                       — FastAPI on Cloud Run
│   ├── main.py                    — /ingest /detect /takedown /athlete/enroll /verify
│   ├── ingest.py                  — keyframes · pHash · embeddings · C2PA sign
│   ├── detect.py                  — two-stage detection (pHash + Vector Search + Gemini)
│   ├── takedown.py                — jurisdiction router + notice filing
│   ├── schema.py                  — Pydantic + Firestore models
│   ├── vector_index.py            — Vertex Vector Search with LOCAL fallback
│   ├── storage.py                 — Firestore with LOCAL fallback
│   ├── prompts/
│   │   ├── verdict.txt            — Gemini verdict system prompt (the novelty)
│   │   ├── deepfake_verdict.txt   — likeness-abuse classifier prompt
│   │   ├── takedown_us.txt        — DMCA §512(c) template
│   │   └── takedown_in.txt        — IT Rules 2021 template
│   ├── requirements.txt
│   └── Dockerfile
├── frontend/                      — React + Vite + Tailwind · EN + HI
│   ├── src/App.tsx                — routes (Athlete / Rights-holder / Verify)
│   ├── src/pages/AthleteView.tsx  — DEFAULT landing (bilingual alerts, opt-in)
│   ├── src/pages/RightsHolderDashboard.tsx (behind auth in prod)
│   ├── src/pages/VerifyPage.tsx   — public Merkle-receipt lookup
│   └── src/i18n.ts                — English + Hindi strings
├── benchmark/
│   ├── generate_variants.py       — seeded adversarial variant generator
│   └── run.py                     — benchmark driver; writes summary.json + per-variant.jsonl
├── data/
│   ├── originals/                 — CC-licensed source clips
│   ├── adversarial/               — generated variants
│   └── case-study/                — Test-Subject Meera sources + logs
└── docs/
    ├── problem_statement.md       — how Aegis scopes PS#1
    ├── solution_brief.md          — architecture, innovations, stack, scale
    ├── why-not-drm.md             — DRM-preempt + jurisdiction
    ├── sdg-alignment.md
    ├── ethics.md                  — deepfake guardrails
    ├── case-study.md              — Test-Subject Meera scenario
    ├── demo-cold-open.md          — replaces first 30 s of demo storyboard
    └── benchmarks.md              — numeric targets + protocol
```

## Quickstart (local, no GCP required)

Both the backend and the variant generator work in a LOCAL mode without any GCP credentials — useful for offline dev and for running integration tests on a laptop.

```
# backend
cd backend
pip install -r requirements.txt
uvicorn backend.main:app --reload --port 8080
# -> http://localhost:8080/healthz

# frontend
cd frontend
npm install
npm run dev
# -> http://localhost:5173
```

`LOCAL` mode uses deterministic mock embeddings, an in-memory vector store, an in-memory storage layer, and a templated mock Gemini response. Every mock path is clearly marked in code (see `AEGIS_INDEX_MODE=LOCAL`, `AEGIS_STORAGE_MODE=LOCAL`, `_mock_*` helpers) — never used in submission, always used in dev loop.

## Production wiring (GCP)

Enable on the GCP project:

- Vertex AI (Gemini + Multimodal Embeddings + Vector Search)
- Cloud Run (API + Jobs)
- Firestore
- Cloud Storage
- Cloud KMS
- Pub/Sub
- Firebase Auth + Hosting

Set (via Cloud Run revision env or local shell):

| Env var | Purpose |
|---|---|
| `VERTEX_AI_PROJECT` | GCP project ID for Vertex AI (Gemini + embeddings + Vector Search). Must be set for real benchmark numbers. |
| `VERTEX_AI_LOCATION` | Vertex region, e.g. `us-central1`. |
| `VERTEX_VECTOR_INDEX_ID` / `VERTEX_VECTOR_ENDPOINT_ID` / `VERTEX_VECTOR_DEPLOYED_INDEX_ID` | The three Vector Search IDs. Create in the Vertex AI console. |
| `AEGIS_INDEX_MODE` | `LOCAL` (in-memory FAISS-style) or `GCP` (Vertex Vector Search). Default `LOCAL`. |
| `AEGIS_STORAGE_MODE` | `LOCAL` (in-memory) or `GCP` (Firestore). Default `LOCAL`. |
| `AEGIS_KMS_MODE` | `LOCAL` (HMAC dev key) or `GCP` (Cloud KMS asymmetric sign). Default `LOCAL`. |
| `AEGIS_KMS_KEY` | Fully qualified Cloud KMS key-version resource name. Required when `AEGIS_KMS_MODE=GCP`. |
| `AEGIS_ANCHOR_MODE` | `EAGER` (flush Merkle root after every leaf) or `DAILY` (scheduled flush). Default `EAGER`. |
| `AEGIS_DEMO_MODE` | `true` enables the demo-only caption-keyword rule in `_mock_verdict` that classifies captions containing "deepfake" / "morph" / "ai-generated" as `DEEPFAKE_MANIPULATION`. **Off by default.** Never set in CI or benchmarks. Use only when recording the scripted demo flow against mock Gemini. |
| `AEGIS_WORKDIR` | Temp directory root for uploaded/extracted frames. Defaults to OS temp. |
| `MOCK_{X,YOUTUBE,META,TELEGRAM}_ENDPOINT` | Full URL (including `/takedown`) of the per-platform Cloud Run honeypot. |
| `GOOGLE_APPLICATION_CREDENTIALS` | Path to service-account JSON, or use Cloud Run's default SA. |
| `ALLOWED_ORIGINS` | Comma-separated CORS origins for the API. Defaults to `*`. |

Build + deploy (example, one-shot):

```
gcloud run deploy aegis-api \
  --source . \
  --region us-central1 \
  --allow-unauthenticated \
  --min-instances=1
```

## Constructed test scenario (read before reviewing the demo)

The flagship demo depicts a **fictional woman cricketer named "Test-Subject Meera"** in a **fictional regional league**. No real athlete, league, or broadcaster is depicted. The full ethics and sourcing standard for the case study is in [docs/case-study.md](docs/case-study.md) — including the `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark rule, the artifact-destruction protocol, and the citation policy for the 2023 Rashmika Mandanna public-incident anchor used in the deck.

## License

Core provenance + athlete view + detection pipeline are licensed under **Apache-2.0** (see [LICENSE](LICENSE)). This is load-bearing for the "not DRM" framing — see [docs/why-not-drm.md](docs/why-not-drm.md) §Licensing posture.

## Benchmarks

Headline Phase-1 targets — full table and protocol in [docs/benchmarks.md](docs/benchmarks.md):

- Recall (retrieved `clip_id` = expected source) on single adversarial transforms: **≥ 0.80** (Phase 1 · fixed thresholds; sweep is Phase 2)
- Precision@5 on Vector Search retrieval: **≥ 0.80**
- End-to-end latency (detection → verdict → DMCA draft): **< 90 s p95**
- Deepfake detection accuracy (zero-shot Gemini on 30-clip set): **≥ 0.80**
- Pipeline integrity (our pipeline, not the platforms): **100%**

## Credits

Built by the Aegis team for the Google Solution Challenge 2026. Thanks to the maintainers of C2PA, DFDC, Celeb-DF, ImageHash, and the Vertex AI SDK.
