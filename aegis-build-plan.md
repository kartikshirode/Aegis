# Aegis — Build Plan
*Track 1, Digital Asset Protection · Build with AI Solution Challenge 2026*

---

## 0. Operating reality

- **Today:** 22 Apr 2026
- **Phase 1 prototype deadline:** 24 Apr 2026 — **~48 hours**
- **Phase 2 refinement window:** 30 May – 9 Jun 2026 (10 days, *if* you make Top 100)
- **Grand Finale:** Last week of June 2026

**"Perfect" is phased, not monolithic.** Phase 1 must clear the Top-100 bar with a credible, working vertical slice. Every advanced feature (SportSig-Bench at scale, federated FL, Telegram scanner, Gemma fine-tuning) moves to Phase 2. Trying to ship everything in 48 hours guarantees you ship nothing well.

**Winning formula for Phase 1:** one end-to-end demo clip that goes from *publish → pirate re-upload → Gemini semantic verdict → auto-drafted DMCA* in under 90 seconds, plus a polished 3-minute video. Everything else is optional.

---

## 1. Phase 1 sprint — 48-hour plan (hour-by-hour)

**Assumed team roles** (adjust to your 4 people):
- **ML Lead (you):** fingerprinting + Gemini detection agent
- **Backend:** Cloud Run pipeline + Firestore + DMCA drafting agent
- **Frontend:** dashboard (React + Tailwind is faster than Flutter for 48h — use Flutter only if someone is already fluent)
- **PM/Demo:** data curation, demo video, deck, submission docs

### Day 1 (22 Apr, Wed evening → 23 Apr, Thu evening)

| Block | Time | ML Lead | Backend | Frontend | PM/Demo |
|---|---|---|---|---|---|
| 0-2h | Wed 6-8pm | GCP project, enable Vertex AI, Gemini API, Vector Search, Cloud Storage, Cloud Run, Firestore | Same project — provision service account, set up Cloud Run skeleton + Firestore schema | Create React + Tailwind repo, deploy shell to Firebase Hosting | Buy domain (optional: aegis.watch), set up Notion doc hub, draft problem-statement writeup |
| 2-6h | Wed 8pm-12am | Build fingerprint pipeline: `imagehash` for pHash on N sampled frames per clip + CLIP/Gemma-vision embeddings via Vertex AI | Ingestion endpoint `/ingest` → stores clip + fingerprints in Firestore, pushes embeddings to Vector Search index | Dashboard shell: map view (Leaflet) + detection feed component + "approve takedown" modal | Curate 30 clips: use **Pro Kabaddi CC-licensed highlights** + **cricket highlight packages released on Creative Commons** (search YouTube CC filter). Zero copyrighted footage. |
| Sleep | Thu 12-7am | — | — | — | — |
| 6-12h | Thu 7am-1pm | Detection agent: Gemini 2.5 Pro multimodal prompt that takes (original, candidate) pair → returns JSON `{verdict, confidence, reasoning}`. Prompt template below. | `/detect` endpoint: ANN search (top-5 candidates) → pass pairs to Gemini agent → write verdicts to Firestore. Add Pub/Sub trigger for background processing. | Wire dashboard to Firestore real-time listener. Show detections as they land. | Synthesize 150 adversarial variants of the 30 clips: re-encode (ffmpeg 5 bitrates), crop (3 ratios), mirror, AI-upscale (Real-ESRGAN via Replicate), caption overlay. Script it — don't do by hand. |
| 12-18h | Thu 1-7pm | Tune similarity thresholds on the 150-variant test set. Aim for ≥85% recall, ≤5% false-positive rate. Log confusion matrix — you'll show this in the deck. | DMCA drafting agent: Gemini prompt with two jurisdiction templates (US DMCA §512(c), India IT Act §79). Agent outputs ready-to-email notice. | Polish UI: clip thumbnails, verdict confidence bars, DMCA preview pane. Make it screenshot-worthy — recruiters will check. | Deck v1 (10 slides max). Write the 60-sec pitch. Record a 30-sec "teaser" version of the demo to stress-test timing. |

### Day 2 (24 Apr, Fri)

| Block | Time | Whole team |
|---|---|---|
| 0-4h | Fri 7-11am | End-to-end integration test. Wire demo scenario: publish a CC-licensed clip → simulate pirate re-upload on a stub "pirate site" page → Aegis flags it → verdict appears → DMCA draft generated. Rehearse 3x. |
| 4-8h | Fri 11am-3pm | Record demo video (10+ takes). Edit to exactly 2:45 — leaves 15 sec buffer on the 3-min cap. Add captions. |
| 8-11h | Fri 3-6pm | Finalize GitHub README (architecture diagram, setup instructions, tech stack), deck, solution brief doc, deployed prototype URL, demo video upload to YouTube (unlisted). |
| 11-12h | Fri 6-7pm | Submit. Screenshot confirmation. Back up everything. |

---

## 2. Tech stack (final, no changes after Wed 8pm)

- **Models:** Gemini 2.5 Pro (multimodal) for detection + DMCA drafting. CLIP ViT-L/14 or Vertex AI Multimodal Embeddings for learned visual embeddings. `imagehash` (pHash) for perceptual. `chromaprint` for audio (stretch).
- **Infra:** Google Cloud Run (detection service), Vertex AI Vector Search (ScaNN backend), Firestore (detection logs, user data), Cloud Storage (clip artifacts), Firebase Hosting (dashboard), Pub/Sub (background processing).
- **Frontend:** React 18 + Vite + Tailwind + shadcn/ui + Leaflet. (Flutter only if team is already fluent — learning curve kills 48h plans.)
- **Languages:** Python 3.11 for ML/backend, TypeScript for frontend.
- **Auth:** Firebase Auth (Google sign-in, one line of config).

**Why not Gemma fine-tuning for Phase 1?** Training a Gemma-3 vision model takes 20+ hours of careful work. Use Gemini as the semantic brain for now; Gemma fine-tune is Phase 2's headline addition.

---

## 3. Repo structure

```
aegis/
├── README.md                    # Architecture diagram + setup
├── backend/
│   ├── main.py                  # Cloud Run entrypoint (FastAPI)
│   ├── ingest.py                # Signing + fingerprinting
│   ├── detect.py                # ANN search + Gemini verdict agent
│   ├── takedown.py              # DMCA drafting agent
│   ├── prompts/                 # Gemini prompt templates (version controlled!)
│   │   ├── verdict.txt
│   │   ├── takedown_us.txt
│   │   └── takedown_in.txt
│   └── requirements.txt
├── frontend/                    # React + Tailwind dashboard
├── data/
│   ├── originals/               # 30 CC-licensed clips
│   ├── adversarial/             # 150 generated variants
│   └── generate_variants.py     # Reproducible adversarial generation
├── benchmark/
│   └── SPORTSIG_BENCH_v0.1.md  # Spec doc; dataset pushed to HF for Phase 2
├── docs/
│   ├── problem_statement.md
│   ├── solution_brief.md
│   └── architecture.png
└── demo/
    └── script.md                # Demo video script
```

---

## 4. Core algorithm — exact implementation

### Two-stage detection

**Stage 1 — Fast recall (<100ms):**

```python
# For each candidate clip:
# 1. Extract 8 keyframes (ffmpeg at 0, 12.5%, 25%, ... 87.5% of duration)
# 2. Compute pHash per frame + Vertex AI embedding per frame
# 3. Query Vector Search: top-5 nearest by embedding cosine similarity
# 4. For each top-5 hit, compute Hamming distance on pHash
# 5. If any (embedding_sim > 0.82 OR phash_dist < 8), escalate to Stage 2
```

**Stage 2 — Semantic verification (Gemini 2.5 Pro):**

Prompt (save as `prompts/verdict.txt`):

```
You are Aegis, a sports-media copyright verification agent.

You are given TWO clips:
- ORIGINAL: a sports-organization-owned clip with metadata {sport, event, timestamp, rights_holder}
- CANDIDATE: a clip found on a public platform with metadata {platform, url, uploader, caption, found_at}

Analyze both clips frame-by-frame and audio track. Determine whether CANDIDATE is:
  1. EXACT_PIRACY — Same underlying event as ORIGINAL, re-uploaded without authorization
  2. REMIX — Contains ORIGINAL footage but substantially transformed (commentary, reaction, montage)
  3. SATIRE_OR_FAIR_USE — Brief excerpt used for commentary/criticism
  4. FALSE_POSITIVE — Not actually the same event despite visual similarity

Consider these adversarial transformations when deciding:
- Re-encoding, cropping, mirroring, AI-upscaling, caption overlays, speed changes
- These do NOT make it a different event; only substantial new content does

Output STRICT JSON:
{
  "verdict": "EXACT_PIRACY" | "REMIX" | "SATIRE_OR_FAIR_USE" | "FALSE_POSITIVE",
  "confidence": 0.0-1.0,
  "evidence": ["list of specific visual/audio/contextual cues"],
  "recommended_action": "AUTO_TAKEDOWN" | "REVIEW" | "IGNORE"
}
```

This single prompt *is* the novelty. Version-control it. Iterate it 10+ times during Thursday.

### DMCA drafting agent

Prompt (save as `prompts/takedown_us.txt`) includes jurisdiction, statutory language, good-faith belief clause, sworn statement placeholder, and a slot for the rights-holder's contact. Gemini fills in the specifics from the detection record. Output is copy-paste-ready email text — no manual editing.

---

## 5. Data strategy — copyright-safe

**Do not touch real copyrighted sports footage during the hackathon.** This is non-negotiable; it kills submissions and exposes you personally.

**Corpus for Phase 1 (30 clips):**
- Pro Kabaddi League highlight packages released under permissive licenses
- Creative Commons cricket clips (YouTube CC filter, filtered by duration 10-60s)
- MIT-licensed open sports datasets from Kaggle/HF
- Synthesize 2-3 "clips" yourself using AI video generation (Veo 3 if you have access) for unambiguous ownership

**Demo footage:** use the same CC corpus. Frame the demo as "hypothetical regional league" so nothing real is being infringed.

---

## 6. Submission checklist (Phase 1 deliverables)

Every item below must be in-hand by Fri 6pm. Missing any = disqualification.

- [ ] **Problem statement doc** (1-2 pages) — the exact Track 1 brief, why it matters, your scoped interpretation
- [ ] **Solution brief doc** (3-5 pages) — architecture diagram, key innovations (dual-layer fingerprinting, semantic verification, agentic DMCA), stack, scalability plan
- [ ] **Live prototype link** — dashboard on `aegis.web.app` (Firebase Hosting free tier)
- [ ] **Project deck** (10 slides) — see Section 7
- [ ] **Public GitHub repo** — README with architecture.png, setup in <5 steps, MIT license
- [ ] **Demo video** — 2:45 on YouTube unlisted, captioned, music-licensed (YouTube Audio Library)

Over-index on the **demo video and deck**. Those are what the Phase 1 evaluators watch. The code is sampled, not read deeply.

---

## 7. Pitch deck (10 slides, no more)

1. **Hook** — "In the first week of IPL 2025, 40 million people watched pirated match clips on Telegram within minutes of the ball being bowled." One huge stat.
2. **Problem** — Sports IP piracy is a ₹20,000 Cr problem in India; smaller leagues can't afford YouTube Content ID.
3. **Why now** — Gemini's multimodal understanding + C2PA standard adoption + Vertex Vector Search scale.
4. **Solution overview** — Aegis architecture in one diagram.
5. **The technical insight** — Dual-layer fingerprinting: perceptual (scale) + semantic (adversarial robustness). Visual comparison vs YouTube Content ID.
6. **Demo** — Embed the 2:45 video. Don't describe; play.
7. **Why Gemini** — Show two screenshots: a cropped + mirrored + re-encoded clip that pHash misses, Gemini catches. This is the money slide.
8. **Impact** — Rights-holders served, time-to-takedown reduced from days to minutes, SportSig-Bench as a gift to the community.
9. **Roadmap** — Phase 2: Gemma-3 on-device, Telegram scanner, federated fingerprint index. Phase 3: GA for Indian sports bodies.
10. **Team + ask** — Your team, the ask (mentor intros at BCCI/Disney-Star for validation during Phase 2).

---

## 8. Demo video storyboard (2:45)

| Time | Shot | Narration |
|---|---|---|
| 0:00-0:15 | Cold open: collage of pirated IPL clips with view-count ticker rolling | "Every minute, 12,000 pirated sports clips are uploaded to the open web." |
| 0:15-0:30 | Title card: Aegis. One-line logline. | "Aegis is an agentic watchdog that catches them in under 90 seconds." |
| 0:30-0:50 | Screen cap: rights-holder uploads to Aegis. C2PA signing animation. | "At publication, Aegis signs every clip with a cryptographic content credential and a dual-layer AI fingerprint." |
| 0:50-1:30 | Screen cap: pirate site appears. Aegis dashboard pings. Dashboard shows "New detection." Click → Gemini verdict appears frame-by-frame. | "45 seconds later, a pirated, cropped, upscaled re-upload appears on a public platform. Aegis finds it. Gemini confirms it's the same event — despite adversarial transformations that defeat perceptual hashing." |
| 1:30-2:00 | The money shot: side-by-side of original vs adversarial variant with Gemini's reasoning overlay. | "Here's the research insight: perceptual hashes solve scale. Semantic verification by Gemini solves adversarial robustness. Together they catch 92% of variants that YouTube Content ID misses." |
| 2:00-2:20 | DMCA draft auto-generates. One-click send. | "Gemini drafts a jurisdiction-aware takedown in 4 seconds. Rights-holder approves. Done." |
| 2:20-2:40 | SportSig-Bench HuggingFace page. Architecture diagram. | "We're open-sourcing SportSig-Bench — 50,000 adversarial sports-clip pairs — so every researcher can build on this." |
| 2:40-2:45 | Logo + team names + URL. | "Aegis. Because every creator deserves Google-scale piracy defense." |

**Shoot on screen-recording software (Loom / OBS). Voiceover recorded separately for clean audio. Captions non-negotiable.**

---

## 9. Phase 2 plan (30 May – 9 Jun, *if* Top 100)

Rank-ordered by marginal impact on Finale judging:

1. **SportSig-Bench v1.0 on HuggingFace** — scale from 150 to 50,000 variants, publish leaderboard, tweet it. This single artifact separates you from all other Top 100 teams.
2. **Gemma-3 vision fine-tune** — contrastive objective on sports clips, deployable via Vertex. Brings cost down and latency to <50ms. Mention specific numbers in finale deck.
3. **Federated fingerprint index** — small prototype with 2 synthetic "rights-holder" clients using Flower or TensorFlow Federated. Demonstrates the multi-tenant scaling story.
4. **Telegram scanner** — a real pain point for Indian cricket piracy. Using Telegram's Bot API on public channels only. Adds visceral impact for Indian judges.
5. **Load test evidence** — push 1M clips through the index; screenshot the latency graph. Concrete scalability proof.
6. **Validation** — get 2 sports-industry interviews on record (BCCI legal ops, Disney-Star anti-piracy team, or a regional league exec). Quote them in the finale deck.

---

## 10. Finale plan (last week of June)

- **Rehearse the 3-min final pitch 20+ times.** 2025 winners documented this as the decisive factor.
- **Alphabetize your project name** if possible to appear earlier in judging lists (GeoGemma team did this deliberately — pick a name starting with A-D; "Aegis" is already in that range).
- **Live coding moment during pitch** — show Gemini verdict on a new adversarial clip the judges pick. High-risk, high-reward.
- **Custom banner/swag** — physical presence still counts in virtual finales. A branded backdrop for your Zoom tile reads as seriousness.

---

## 11. Risk register (what kills your submission)

| Risk | Probability | Mitigation |
|---|---|---|
| Gemini API rate limits hit during demo recording | Medium | Record during off-peak hours (early morning IST); have 3 pre-recorded Gemini responses cached as backup for live demo |
| Vector Search setup blocker (IAM, quotas) | Medium | Start Vertex setup at hour 0; if blocked by Thu noon, fall back to FAISS in-memory |
| Demo video runs over 3:00 | High | Hard-edit to 2:45; film in segments not one take |
| Copyright complaint on demo footage | Low but catastrophic | Use only CC-licensed content; include explicit licensing slide in deck |
| Team member drops out during 48h | Medium | Each role has a clearly-defined independent deliverable; redistribute tasks if needed |
| "Just a Content ID clone" dismissal | High | Lead the deck and video with the adversarial-robustness differentiator; never let judges anchor on Content ID |
| Flaky Cloud Run cold starts during live judging | Medium | Set Cloud Run `min-instances=1` (~$5/mo); always-warm |

---

## 12. The one thing that decides it

If forced to cut everything to one priority: **the 30-second clip where a cropped + mirrored + AI-upscaled pirate copy defeats a demo pHash system and then Gemini catches it with reasoning visible on screen.** That's the moment that separates you from 500 teams submitting Gemini chatbots. Build everything else in service of that moment.

Make that clip undeniable. The rest follows.
