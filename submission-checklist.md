# Phase-1 Submission Checklist — Aegis

**Deadline:** 24 Apr 2026. Every item on this checklist is load-bearing for either scoring or ethics. Check everything off before the submission portal closes.

## Required submission artifacts

- [ ] **Live MVP URL** — Firebase Hosting, custom subdomain (e.g. `aegis.web.app`). Loads in <3s on a cold cache. Default landing page is the athlete view.
- [ ] **Public GitHub repo** — README renders cleanly on github.com, LICENSE present, `.gitignore` excludes secrets and media artefacts.
- [ ] **2-minute demo video** — exactly **2:45**, hosted unlisted on YouTube, captions (EN top + HI bottom) burned in, `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark visible on every frame that shows the manipulated clip. Opens with the athlete-harm moment, not a league logo.
- [ ] **10-slide pitch deck** — PDF + editable source. Slide #2 is "What this is NOT" (DRM preempt). Slide #3 is SDG framing with 5+16 in the primary tier.
- [ ] **Problem statement doc** — `docs/problem_statement.md`
- [ ] **Solution brief doc** — `docs/solution_brief.md`

## Strategic / differentiating docs (submit as a bundle)

- [ ] `docs/why-not-drm.md` — DRM preempt + jurisdictional posture
- [ ] `docs/sdg-alignment.md` — SDG 5+16 primary, 8+9 secondary
- [ ] `docs/ethics.md` — deepfake guardrails
- [ ] `docs/case-study.md` — Test-Subject Meera scenario
- [ ] `docs/demo-cold-open.md` — the revised opener
- [ ] `docs/benchmarks.md` — numeric targets + protocol
- [ ] `docs/architecture.md` — architecture diagram + service map

## Engineering artefacts

- [ ] `backend/` compiles and runs; `pytest tests/` passes green
- [ ] `backend/prompts/*.txt` — all four prompts shipped and version-controlled
- [ ] `services/agents/` — per-platform agents in place
- [ ] `services/mock_platforms/app.py` — deployed to 4 Cloud Run URLs
- [ ] `services/crawler/` — runs against the seed file and submits to `/detect`
- [ ] `benchmark/generate_variants.py` and `benchmark/run.py` — numbers written to `data/benchmark-results/summary.json`
- [ ] `demo/seed_demo.py` — runs end-to-end and prints a JSON summary
- [ ] `docs/dataset-cards/dfdc.md` and `celeb-df.md` — populated

## Case-study artefacts (ethics-defense)

- [ ] `data/case-study/sources.md` — every portrait, voice, and footage source listed with license ID + URL
- [ ] `data/case-study/generation-log.md` — operator, date, tooling, input hashes, output hash
- [ ] `data/case-study/destruction-log.md` — ready to be populated after Phase-1 or Grand Finale
- [ ] Constructed clip carries `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark at 100% opacity, bottom-right

## SDG + rubric alignment (checkpoint before submission)

- [ ] Slide #3 of the deck lists SDG 5 and SDG 16 in the primary (larger, bolder) tier
- [ ] Slide #2 is the DRM-preempt contrast table
- [ ] Slide #8 cites published Phase-1 benchmark numbers, not claims
- [ ] Demo video opens on human harm; "IPL piracy" statistics (if used at all) appear only after 0:30
- [ ] README top-fold frames beneficiaries as "athletes and fans, not the leagues"

## Benchmark numbers actually present (not claimed)

Before submit, run the benchmark against the variants set and confirm:
- [ ] `data/benchmark-results/summary.json` exists and has `recall_overall`, `per_transform`, `latency_ms_p50`, `latency_ms_p95`
- [ ] Numbers copied into `docs/benchmarks.md` replacing placeholder targets where the actual exceeds or equals the floor
- [ ] Any missed target has a one-line postmortem in `docs/benchmark-postmortem.md` (create the file if needed)

## Final human checks (last 30 minutes before submit)

- [ ] **Pre-flight: `curl $API_URL/demo/status` returns `gemini_live: true` AND `vector_search_configured: true`.** If either is `false`, the demo will silently fall back to LOCAL mocks and the numbers you record will not be real. Fix env vars before going further.
- [ ] Open MVP URL on a clean Chrome profile (incognito). Verify athlete view renders; verify Hindi toggle works; verify `/verify/<some-id>` returns a structured result.
- [ ] Open GitHub repo, check README preview, check LICENSE present, verify CI (if set up) is green.
- [ ] Play the demo video once end-to-end on phone speakers — confirm captions are legible at small size.
- [ ] Verify all `docs/` files render on GitHub without broken links.
- [ ] Screenshot the Solution Challenge submission confirmation and store it in a shared drive folder.

## What we explicitly do NOT submit

- The generated Test-Subject Meera clip as a standalone file. It lives inside the demo video (with watermark) only.
- Any real athlete's likeness. Any real league's footage. Any copyrighted material without an explicit CC license.
- Real platform credentials. The `MOCK_*_ENDPOINT` vars point only at our own honeypot services.
