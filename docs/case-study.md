# Flagship Case Study — "Test-Subject Meera"

The 3-minute demo must show a human-harm moment. This document specifies exactly what we demo, where the material comes from, and the anonymization + ethics rules that keep the scenario defensible.

## The scenario, in one sentence

A deepfake clip of a fictional woman cricketer ("Test-Subject Meera") appearing to make a match-fix admission is seeded on a controlled test domain; Aegis detects it, the athlete receives a Hindi-language alert, takedown notices are filed across four platform endpoints, the propagation graph renders, and the `/verify` page shows the Merkle-anchored receipt.

## Why this scenario (not a corporate piracy one)

- Leads the pitch with **athlete harm**, not corporate IP loss. Anchors judges on SDG 5 + 16 in the first 30 seconds.
- Exercises every pillar end-to-end in a single ~90-second walkthrough: provenance (original was signed), detection (crawler finds the leak), classification (labelled `deepfake_manipulation`), deepfake defense (athlete alert), agentic takedown (filed across 4 mock endpoints), audit (Merkle receipt on `/verify`).
- Differentiates from every other PS#1 entry, which will default to a "pirated IPL clip" corporate piracy scenario.

## The public-incident anchor

The non-athlete anchor used to establish the harm pattern (in the deck, not the live demo) is the **2023 deepfake incident targeting Indian actor Rashmika Mandanna**. This incident:

- Was extensively covered in mainstream Indian media (cite news sources at submission time; do not link in this file to avoid link-rot).
- Catalyzed India's 2023 advisory on synthetic media under the IT Rules 2021.
- Established public awareness of non-consensual deepfakes of women public figures in the Indian context.

We reference this incident as *prior reporting*. We do not rehost, regenerate, or re-circulate any media from the incident. Any image of the subject used in the deck comes from already-public, non-manipulated press photography with clear source citation.

## The constructed athlete persona: "Test-Subject Meera"

- **Name:** prefixed `Test-Subject` to foreclose any real-person ambiguity even if a real athlete named "Meera" with a similar surname surfaces later. The on-screen lower-third in every demo frame reads `Constructed test scenario · Test-Subject Meera (fictional)` — no exceptions.
- **Likeness:** composed from CC-0 stock portraits. Specific source(s) will be cited in the submission repo under `data/case-study/sources.md`.
- **Sport:** cricket (the sport with the strongest India piracy/deepfake pattern, keeping the narrative locally credible).
- **Role:** bowler in a fictional regional women's league, also fictional. League name will also be prefixed `Test-League` for the same reason.

## The manipulated clip

- **Content:** ~20-second video of "Test-Subject Meera" appearing to admit to receiving a match-fix payment.
- **Production:** generated offline on a developer machine using DFDC-adjacent open tooling. Not generated via any Google or commercial API. Not hosted or transmitted via the product pipeline.
- **Labelling:** the generated clip embeds a visible watermark `CONSTRUCTED TEST SCENARIO · NOT REAL`. The watermark is **never** removed — not in the dashboard, not in the propagation-graph thumbnail, not in the takedown-notice preview. Every surface that shows the manipulated clip shows the watermark. This is deliberate: the product cannot strip a safety watermark on its own content without undermining the ethics claim it rests on.
- **Distribution:** seeded only on a controlled test domain we operate (e.g., `aegis-test-domain.example`). Never uploaded to any real platform. After Phase 3, the clip file is destroyed and the SHA-256 of the destroyed artifact is logged in `data/case-study/destruction-log.md`.

## The demo storyline (sequenced for 90 seconds)

1. **Publishing** (0:00–0:15). A fictional broadcaster publishes the original, clean match footage of Test-Subject Meera to Aegis. The C2PA content credential is signed and visible on hover.
2. **Attack** (0:15–0:25). A bad actor uploads the manipulated clip to our controlled test domain. This is the only moment the watermarked constructed clip is shown full-screen.
3. **Detection** (0:25–0:45). Aegis crawler finds the clip. pHash misses; embeddings + Gemini catch it. Verdict: `deepfake_manipulation · confidence 0.94`. Reasoning is visible on screen.
4. **Alert** (0:45–1:00). Athlete-facing view, in Hindi + English, shows a red alert: *"आपकी छवि का दुरुपयोग हुआ है / Your likeness has been misused."* One-click dashboard transitions to takedown drafting.
5. **Takedown** (1:00–1:20). ADK agents draft platform-specific notices for four mock endpoints (we stand up honeypot services returning valid structured receipts). India-hosted mock uses the IT Rules 2021 template; US-hosted mock uses the DMCA §512(c) template. Notices are filed. Receipts persist.
6. **Propagation + audit** (1:20–1:30). The propagation graph renders showing where the clip appeared and how it spread across the four mocks. `/verify` page displays the Merkle-anchored receipt of the takedown.

## Sourcing standard checklist (for submission)

- [ ] `data/case-study/sources.md` — provenance for every stock image used to compose the Test-Subject Meera likeness, with license SPDX identifier and original URL.
- [ ] `data/case-study/generation-log.md` — tooling, date, machine, operator for the generated manipulated clip. Includes SHA-256 of the final artifact.
- [ ] `data/case-study/destruction-log.md` — to be populated post-Phase-3 with destruction confirmation.
- [ ] `docs/case-study.md` (this file) — the ethics and narrative rationale.
- [ ] Deck slide with citation for the 2023 Rashmika Mandanna incident (news source + India advisory reference).

## What will never be in the demo

- Any real athlete's likeness, manipulated or not.
- Any copyrighted league footage.
- Any real platform as the target of a real takedown notice during the demo.
- Any manipulated clip without the `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark visible outside the in-dashboard view.
