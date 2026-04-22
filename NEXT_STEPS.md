# Aegis — Next Steps Walkthrough

Everything below is work **only a human operator can do**: install tools, touch GCP, source copyrighted material under a license check, stand in front of a camera, etc. The code is complete.

Rough total time: **8–12 focused hours**, spreadable across team members. Do the steps in order — each one unblocks the next.

---

## 0. Final engineering to-dos (5 minutes each, can skip if you trust the audit)

- [-] Install **ffmpeg** on Windows (required for the variant generator, the demo clip pipeline, and the integration tests):
  ```powershell
  winget install Gyan.FFmpeg
  # reopen shell, then verify:
  ffmpeg -version
  ```
- [-] Confirm tests pass (after ffmpeg install all 18 should run, not just 13):
  ```powershell
  cd "c:\Users\Kartik\Documents\Kartik\EDU\Projects\Solution Challenge"
  pip install -r backend/requirements.txt
  python -m pytest tests/ -v
  ```
  Expect: `18 passed`, zero skipped, zero failed.  --- 19 passed in 6.91s

---

## 1. Decide the brand question (5 minutes, blocks everything downstream)

The audits flagged this three times. The code and README everywhere say **Aegis**. My earlier planning doc used **Pramāṇ** as a working name. **Pick one.**

**Recommendation:** keep **Aegis**. The whole repo, the UX, the env vars, the user-agent string, the Python package names, and the team's internal plan file all already say Aegis. Pramāṇ exists only in my planning note under `~/.claude/plans/` that judges will never see.

If you pick Aegis, no code changes needed — you're done.

If you pick Pramāṇ, tell me and I'll run a consistent rename across code, README, i18n strings, deck, demo script, and submission checklist in one pass. **Do NOT ship with both names visible** — judges will read it as confusion.

___ Keep Aegis

---

## 2. Source the sports-media corpus (60–90 minutes)

The benchmark, the demo, and the case-study scenario all need real video files. The repo ships zero video on purpose — everything must be license-verified by a human.

### 2a. 30 "clean original" clips (for the benchmark + demo publishing step)

**Automated** via `scripts/download_corpus.py` — pulls 30 sport clips from the **HMDB-51** dataset (CC-BY-4.0, Serre Lab, Brown University) via the `divm/hmdb51` HuggingFace mirror. No manual YouTube-CC browsing.

```powershell
python scripts/download_corpus.py
# → 30 mp4s under data/originals/match-NN.mp4 (4.3 MB total)
# → data/originals/LICENSES.md with CC-BY-4.0 attribution + residual-copyright clause
```

Rerun is idempotent (skips already-downloaded files).

**What the corpus is for (read before relying on it):**
- Benchmark only. The clips exercise `backend/detect.py` + `benchmark/run.py` to measure recall / match-rate / precision under adversarial transforms. They never reach any public output.
- **Not redistributed.** `.gitignore` excludes `data/originals/*.mp4` — they don't ship in the public GitHub repo.
- **Not shown in the 2:45 demo video.** HMDB-51 was compiled from mixed sources (some YouTube UGC, some broadcast, some DVD) and individual clips may retain residual copyright beyond the dataset-level CC-BY-4.0. On-screen demo content comes from team-generated Veo 3 footage + the Test-Subject Meera constructed clip (§2b). See `data/originals/LICENSES.md` for the full residual-copyright treatment.

**If your reviewer needs a CC-0-clean benchmark corpus** (e.g., rights-holder partnership demo), swap HMDB-51 for Pexels API downloads in the script. The rest of the pipeline is indifferent to the source.

### 2b. Constructed Test-Subject Meera persona (30–60 minutes)

This is the most sensitive deliverable. Follow `docs/case-study.md` + `data/case-study/generation-log.md` exactly:

1. **Compose the persona likeness** from CC-0 stock portraits:
   - [Unsplash Free](https://unsplash.com/) → search: "portrait woman" → filter: `Free to use`
   - [Pexels](https://www.pexels.com/search/portrait%20woman/) → confirm CC-0 license per image
   - [Wikimedia Commons](https://commons.wikimedia.org/) → filter by public domain
   - Save each source image + a screenshot of its license badge to `data/case-study/sources/`
2. **Write the sources in** `data/case-study/sources.md` (template already in the file).
3. **Generate a ~20-second "match-fix admission" clip** using open-source DFDC-adjacent tooling on a developer machine, offline. Do NOT use any commercial API. Burn in the `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark at 100% opacity, bottom-right, 48pt.
4. **Log to** `data/case-study/generation-log.md` (template already in the file). Record: operator name, UTC datetime, machine hostname, tooling + versions, input asset SHA-256s, output SHA-256.
5. **Place the clip** at `data/case-study/generated/constructed-meera-clip.mp4`. Never upload it to any public host.

> **Ethics non-negotiable:** if you cannot source + log a clip under these terms, drop the deepfake pillar from the demo. A corner-cut here poisons the entire "Alignment With Cause" story.

### 2c. Generate the adversarial variant corpus (5 minutes)

Once `data/originals/` has ≥ 30 clips:

```powershell
python benchmark/generate_variants.py `
  --originals data/originals `
  --out data/adversarial `
  --seed 2026 `
  --n-originals 30 `
  --chain-samples 50
```

Expect ~240 variants + a `manifest.json`.

---

## 3. Stand up GCP (60–90 minutes)

### 3a. Prerequisites

- [ ] Install **gcloud CLI**: https://cloud.google.com/sdk/docs/install
- [ ] Install **Firebase CLI**: `npm install -g firebase-tools`
- [ ] `gcloud auth login` + `gcloud auth application-default login`
- [ ] `firebase login`

### 3b. Create + configure project

```powershell
# Pick a project ID (must be globally unique)
$env:PROJECT_ID = "aegis-sc2026-<your-suffix>"
$env:REGION = "us-central1"

gcloud projects create $env:PROJECT_ID
gcloud config set project $env:PROJECT_ID

# Link billing (replace ACCOUNT_ID with yours — find via `gcloud billing accounts list`)
gcloud billing projects link $env:PROJECT_ID --billing-account=<ACCOUNT_ID>

# Enable APIs, create KMS key, deploy 4 mocks + API + crawler:
bash infra/deploy.sh
```

**Expect**: script finishes in 8–15 minutes with 5 Cloud Run URLs and a KMS key version printed.

### 3c. Create the Vertex AI Vector Search index (manual, ~10 min wait)

`infra/deploy.sh` does **not** do this — index deployment is multi-minute and easier in the console.

1. [Vertex AI Console → Vector Search](https://console.cloud.google.com/vertex-ai/matching-engine) → Create Index
2. Settings:
   - **Algorithm**: ScaNN (approximate)
   - **Dimensions**: 1408
   - **Distance**: Cosine
   - **Shard size**: SMALL (cheapest)
3. Wait for index to be `READY` (~8 minutes).
4. Create an **Index Endpoint** in the same region.
5. **Deploy the index to the endpoint** (~10 minutes).
6. Copy the three IDs and re-export:
   ```powershell
   $env:VERTEX_VECTOR_INDEX_ID = "..."
   $env:VERTEX_VECTOR_ENDPOINT_ID = "..."
   $env:VERTEX_VECTOR_DEPLOYED_INDEX_ID = "..."
   ```
7. Re-run `bash infra/deploy.sh` — it will pick up the IDs and update the Aegis API's env.

### 3d. Firebase Hosting (5 minutes)

```powershell
cd frontend
firebase init hosting   # pick the project; public=dist; SPA=yes; overwrite=no
npm install
# Put the API URL in frontend/.env.production:
#   VITE_AEGIS_API_BASE=https://aegis-api-xxxxx-uc.a.run.app
#   VITE_AEGIS_DOCS_BASE=https://github.com/<org>/<repo>/blob/main/docs
npm run build
firebase deploy --only hosting
```

Copy the hosting URL.

### 3e. Sanity check GCP mode

```powershell
curl https://aegis-api-<hash>.a.run.app/demo/status
```

Must return:
```json
{
  "index_mode": "GCP",
  "storage_mode": "GCP",
  "kms_mode": "GCP",
  "gemini_live": true,
  "vector_search_configured": true,
  "mock_endpoints": {"x": true, "youtube": true, "meta": true, "telegram": true}
}
```

If any value is `LOCAL` or `false`, go back and fix the env on the Cloud Run revision **before doing anything else** (especially before running the benchmark).

---

## 4. Run the real benchmark (20 minutes)

Once GCP is up and `data/originals/` + `data/adversarial/` are populated:

```powershell
python benchmark/run.py `
  --originals data/originals `
  --variants data/adversarial `
  --api-base https://aegis-api-<hash>.a.run.app `
  --ingest-first
```

This hits live Vertex — costs a few rupees in Gemini calls. Expect it to finish in 10–30 minutes.

Output: `data/benchmark-results/summary.json`. Copy the actual numbers into:
- `docs/benchmarks.md` — replace the "target" column entries where actual ≥ target; leave target column if we miss (with a one-line postmortem in `docs/benchmark-postmortem.md`, create the file if needed)
- `deck/deck.md` slide 8 — replace the `≥ 0.80` etc. with actuals
- Slide the same numbers into `README.md` Benchmarks section

**Do not record the demo or submit the deck until this step is done.** The whole "numbers, not claims" story hangs on it.

---

## 5. Record the demo video (90 minutes including retakes)

### 5a. Pre-flight (last time, I promise)

```powershell
curl https://aegis-api-<hash>.a.run.app/demo/status
```

All values must be GCP/true. See `docs/demo-cold-open.md` end-of-file for the exact check.

### 5b. Rehearse the scenario

Run `demo/seed_demo.py` against the live API 3+ times to confirm deterministic output:
```powershell
python demo/seed_demo.py `
  --original data/originals/<one-CC-licensed-clip>.mp4 `
  --leak data/case-study/generated/constructed-meera-clip.mp4 `
  --api-base https://aegis-api-<hash>.a.run.app
```

Each run should print a JSON summary with a verdict, four takedown notices (one per platform), and a Merkle root.

### 5c. Record

Follow `demo/script.md` shot-by-shot. Key rules:
- Cold open leads with the **athlete-harm moment**, not an IPL piracy stat
- Every frame that shows the manipulated clip carries the `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark
- Bilingual captions (English top + Hindi bottom) on every spoken line
- **Exactly 2:45**. Record in segments (don't try one take). Edit in your tool of choice (OBS + Shotcut, DaVinci Resolve, CapCut).

Upload to YouTube **Unlisted**. Grab the URL.

---

## 6. Build the deck (45 minutes)

Follow `deck/deck.md` slide-by-slide. Tools:
- Google Slides (easiest for collaboration + judges-friendly export)
- Keep dark neutral background, white headlines, one accent red only for athlete-harm callouts
- Slide 6 is the YouTube embed — paste the unlisted URL
- Export both PDF and a Google Slides link for submission

---

## 7. Populate the last bits of documentation (15 minutes)

- [ ] Fill in `data/case-study/sources.md` — every portrait/voice/footage asset listed, with license ID + URL
- [ ] Fill in `data/case-study/generation-log.md` — operator, datetime, hashes (skip destruction-log until after Phase 3)
- [ ] Add two lines to `data/originals/LICENSES.md` for the sports corpus licenses
- [ ] If the benchmark hit any targets under the floor, write `docs/benchmark-postmortem.md` with a one-line honest note

---

## 8. Ship the repo to GitHub (15 minutes)

- [ ] Confirm `.gitignore` excludes `Audit v*.md`, `data/originals/*.mp4`, `data/adversarial/*.mp4`, `data/case-study/generated/`, secrets (`.env`, `*.key`, `gcp-sa*.json`).
- [ ] `git add` — review what's about to be committed; **do not commit the constructed clip, the originals, or any `Audit v*.md` file**.
- [ ] `git commit -m "Aegis — Phase 1 submission"`
- [ ] Create a public GitHub repo; push.
- [ ] Verify the README renders at `https://github.com/<org>/<repo>` and all `docs/` links work.
- [ ] Verify the footer doc-links on the live Firebase URL resolve (set `VITE_AEGIS_DOCS_BASE` to your GitHub `/blob/main/docs` URL if you haven't).

---

## 9. Submit (10 minutes)

Open `submission-checklist.md`, go top to bottom, check every box, then:

1. Submit on the Hack2skill portal with:
   - **Live MVP URL** (Firebase Hosting URL)
   - **Public GitHub URL**
   - **YouTube demo video URL** (unlisted is fine if the portal accepts)
   - **Deck** (PDF + editable link)
   - **Problem statement doc** (`docs/problem_statement.md`)
   - **Solution brief doc** (`docs/solution_brief.md`)
2. Screenshot the submission confirmation. Save to team drive.
3. Tweet / post / whatever. Sleep.

---

## What's still on the roadmap (Phase 2, ignore for now)

Do NOT do these before 24 Apr submission — they are tracked so nobody relitigates them in the final hours:

- Wire `backend/prompts/deepfake_verdict.txt` escalation path on borderline DEEPFAKE_MANIPULATION verdicts
- Fine-tuned deepfake classifier head (Vertex AI custom model, DFDC-trained)
- Threshold sweep in `benchmark/run.py --sweep` → real ROC curves → honest "recall at ≤ 5% FPR" numbers
- Google ADK multi-agent orchestration replacing the single-process `services/agents/` registry
- Chunked / Cloud-Storage-URI Gemini input path for clips > 7 MB
- `/demo/status` behind auth in production
- Module-level `AegisStore` → dependency-injected for cleaner test isolation
- Real platform submission (actual X / YouTube / Meta / Telegram takedown APIs) — requires rights-holder standing and their API keys
- Cross-border notice reciprocity
- Federated fingerprint index
- SportSig-Bench 50K-pair release on HuggingFace
- Telegram channel scanner (Telegram's Bot API over public channels)
- Load test evidence at 1M-clip scale

Everything on this list is mentioned in `deck/deck.md` slide 9 (Roadmap). Judges reward a team that can name Phase 2 concretely.

---

## Emergency contact

If something in this walkthrough breaks:
1. Run `curl <api-url>/demo/status` — if it reports `LOCAL` anywhere, you forgot an env var on the Cloud Run revision. Fix via `gcloud run services update aegis-api --update-env-vars KEY=VALUE`.
2. Run `python -m pytest tests/ -v` — if it fails, the backend has regressed; revert your last change.
3. Run `python demo/seed_demo.py --api-base http://localhost:8080 --original data/originals/any.mp4 --leak data/case-study/generated/constructed-meera-clip.mp4` against a local `uvicorn backend.main:app` — if this works locally but not against Cloud Run, the issue is GCP config.

The whole pipeline is designed to fail loud (clear exceptions) rather than silently — if something breaks and the logs are quiet, the bug is a new one, not a config drift.

Good luck.
