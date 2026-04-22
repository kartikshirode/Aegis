# Aegis — Phase-1 Deck (10 slides)

Keep it tight. One idea per slide. This document is a producible spec — every slide has a single purpose, the verbatim headline, the on-screen bullet points (limit 5), and a 15-second speaker track.

**Visual direction:** dark neutral background (#0f172a), white serif headline, sans for body, one accent red (#c53030) used only for athlete-harm callouts. Bilingual captions (English top, Hindi bottom) where the slide serves a narrative beat. Team logo bottom-right of every slide, kept small.

**Total speaking time budget:** 3:00 (pitch) or 2:45 (video). The video embed of the demo occupies slide 6 — the rest must fit in the remaining ~45 seconds of voiceover on the other 9 slides.

---

## Slide 1 — Hook (human harm, not piracy stat)

> **"A deepfake said she fixed the match."**
> (एक डीपफेक ने कहा कि उसने मैच फिक्स किया।)

- Image: darkened freeze-frame, woman athlete silhouette, "CONSTRUCTED TEST SCENARIO · NOT REAL" watermark visible bottom-right.
- Subheadline: *In 2026, this is the opening shot of the sports-integrity story — and no one is catching it in time.*

*Speaker (15s):* "In 2026, a deepfake of a woman athlete saying she fixed a match circulates for eight hours before anyone corrects it. That eight hours is where Aegis exists. This is the problem we chose to solve — and it is not the corporate piracy problem."

---

## Slide 2 — What this is NOT (DRM pre-empt)

> **"Not DRM. Not content policing."**

| | Traditional DRM | Content Credentials (C2PA) | **Aegis** |
|---|---|---|---|
| Restricts playback | ✓ | | |
| Attests origin | | ✓ | ✓ |
| Detects in the wild | | | **✓** |
| Detects deepfakes | | | **✓** |
| Files per-platform takedowns | | | **✓** |
| Opt-in for the athlete | N/A | N/A | **✓** |
| Primary beneficiary | Rights-holders | Publishers + consumers | **Athletes + fans** |

*Speaker (20s):* "Before we show what Aegis does, here is what it is not. DRM restricts who can play content. Aegis attests what content is real — opt-in for the athlete, useless against paying consumers, and built first for athletes and fans, not the leagues."

Link footer: `docs/why-not-drm.md`.

---

## Slide 3 — SDG framing

> **"SDG 5 · SDG 16 · SDG 8 · SDG 9"**

- **Primary** (bold, bigger):
  - **SDG 5 — Gender Equality.** Non-consensual deepfakes disproportionately target women.
  - **SDG 16 — Peace, Justice, Strong Institutions.** Fabricated sport media is a misinformation vector.
- **Secondary** (smaller):
  - SDG 8 — athlete and creator livelihoods.
  - SDG 9 — trustworthy media infrastructure.

Small footnote on the 2023 MeitY advisory on synthetic media under the IT Rules 2021.

*Speaker (15s):* "The SDG alignment is deliberate. Primary: gender equality and institutional trust. Secondary: decent work and innovation. Links to `sdg-alignment.md` and the Indian synthetic-media advisory it maps to."

---

## Slide 4 — Solution overview (the architecture, one diagram)

> **"Four pillars. One authenticity layer for sport."**

Mermaid or exported diagram from `docs/architecture.md`. Four labelled pillars across the bottom — Provenance at source · Detection + Classification · Deepfake & likeness defense · Agentic takedown + audit trail.

*Speaker (15s):* "Four pillars. C2PA provenance at publication. Two-stage detection in the wild. Deepfake defense as the primary human-harm surface. Per-platform agentic takedown with a cryptographically verifiable audit trail."

---

## Slide 5 — The technical insight (the "money" technical slide)

> **"Perceptual hash solves scale. Gemini solves adversarial robustness."**

Two columns:
- **Left — a cropped, mirrored, re-encoded, AI-upscaled clip.** pHash distance: 31 (above threshold, would miss). YouTube Content-ID-style would miss this.
- **Right — same clip.** Vertex AI multimodal embedding cosine: 0.88. Gemini 2.5 Pro verdict (JSON excerpt): `{"verdict": "EXACT_PIRACY", "confidence": 0.90, ...}`.

*Speaker (15s):* "Perceptual hashing is fast at scale and brittle under adversarial edits. Multimodal embeddings plus a Gemini verdict agent restore recall — with transparent reasoning in the output."

---

## Slide 6 — Demo (embed video)

> **"90 seconds, end to end."**

Full-bleed embed of the 2:45 demo video. No other content on slide.

*Speaker (0s; the video speaks):* let the video play.

See `demo/script.md` for the full 2:45 storyboard. Cold open replaces §8 of `aegis-build-plan.md` — see `docs/demo-cold-open.md`.

---

## Slide 7 — Why Gemini (the single differentiator)

> **"One prompt. Six verdicts. One action routing."**

Show `backend/prompts/verdict.txt` first 25 lines as a graphic (monospace, syntax-highlighted), with a callout arrow pointing to the action-routing block.

*Speaker (20s):* "This prompt is part of the system, not prose. Six-label verdict space, strict JSON, action routing with published confidence thresholds. It is version-controlled and iterated like a model. This is the single artefact that separates a thoughtful submission from a ChatGPT wrapper."

---

## Slide 8 — Impact + Benchmarks

> **"Measurable, not claimed."**

Published Phase-1 targets from `docs/benchmarks.md`:
- Recall (retrieved clip_id = expected source) on single adversarial transforms: **≥ 0.80** (fixed thresholds; threshold sweep is Phase 2)
- Precision@5 on Vector Search retrieval: **≥ 0.80**
- End-to-end latency (detect → verdict → DMCA draft): **< 90 s p95**
- Deepfake detection accuracy (zero-shot Gemini, 30-clip set): **≥ 0.80**
- Pipeline integrity: **100%** (our pipeline, not the platforms)

Small caption: "Exact numbers computed on held-out set are in `docs/benchmarks.md` and at the live `/benchmarks` page."

*Speaker (15s):* "Every target is a floor. Where we miss, we publish the miss."

---

## Slide 9 — Roadmap

> **"Phase 2 · Phase 3."**

- **Phase 2:** SportSig-Bench (50K adversarial pairs on HuggingFace) · Gemma-3 vision fine-tune · federated fingerprint index · Telegram channel scanner · partner validation interviews.
- **Phase 3:** GA for one Indian sports body (women's cricket or regional football) · full ADK multi-agent orchestration · cross-border notice reciprocity.

*Speaker (10s):* "Phase 2 separates us from 100 other Top-100 teams: open the benchmark, ship Gemma fine-tune, add federated indexing. Phase 3 is GA for an Indian women's or regional league — an underserved segment we have the ethics posture to serve."

---

## Slide 10 — Team + ask

> **"We built Aegis for the ones most at risk, first."**

- Four team members: names, roles, one-line specialty each.
- One line of credits: "Thanks to maintainers of C2PA, DFDC, Celeb-DF, Vertex AI SDK."
- **Ask:** mentor introductions at BCCI legal-ops, Disney-Star anti-piracy, or the ICC women's cricket body for Phase-2 partner validation.
- URL: aegis.example / github.com/aegis-team/aegis.

*Speaker (10s):* "Our ask for Phase 2 is one mentor introduction at a rights-holder or a women's sport body so we can validate the athlete-first framing with real partners."

---

## Production notes

- Export each slide at 1920×1080. Keep the team logo bottom-right consistent.
- Slide 1, 2, 3, and 5 carry the strategic weight — if slide budget shrinks, cut slide 9 (roadmap) first, never these four.
- Slide 6 is the video slide; if the video fails, fallback is a 30-second live walk-through of `demo/seed_demo.py` output on terminal — documented as a fallback in `demo/script.md`.
- Caption every speaker-track line for accessibility, and because judges review submissions asynchronously.

## Narrative arc

Slide 1 is the emotional anchor. Slide 2 immediately neutralises the DRM dismissal. Slide 3 locks SDG framing. Slides 4–8 are the technical case. Slide 9 is the multi-year belief. Slide 10 is the ask.
