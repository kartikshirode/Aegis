# Demo Script — Aegis, 2:45

The 2:45 video is the submission's single most important asset. This script consolidates `docs/demo-cold-open.md` (beats 0:00–0:30) with the remainder of `aegis-build-plan.md` §8, adjusted to put the athlete view first and the jurisdiction-aware takedowns visible.

**Record this way:**
- Screen capture with OBS at 1920×1080. 30 fps is enough.
- Voiceover recorded separately in a quiet room; mix under -3 dB ducking for on-screen UI audio.
- Captions (burned-in, English top + Hindi bottom) — non-negotiable.
- Music bed: YouTube Audio Library track, low-volume. Silence for the first 8 seconds.

---

## Full storyboard

| Time | Shot (visual) | Narration (VO) | Caption |
|---|---|---|---|
| **0:00–0:08** | Dark frame. Text appears one word at a time in white: *"A video circulates of a woman athlete making a match-fix admission."* · Hindi transliteration appears underneath. | (silent — only the words) | EN: "A video circulates of a woman athlete making a match-fix admission." · HI: "एक महिला खिलाड़ी का वीडियो फैल रहा है जिसमें मैच फिक्सिंग की बात है।" |
| **0:08–0:15** | Split screen. Left: the constructed clip (watermark `CONSTRUCTED TEST SCENARIO · NOT REAL` clearly visible). Right: a news-ticker of already-public reporting on the 2023 Rashmika Mandanna incident with citation line. | "It's a deepfake. She never said it. The clip is already across four platforms before anyone notices." | bilingual |
| **0:15–0:22** | Title card: **Aegis**. Subtitle: *"Cryptographic provenance, deepfake defense, and agentic takedown — for the people whose likenesses are at stake."* | "Aegis is an authenticity layer for sport — built for the athletes and fans, not the leagues." | bilingual |
| **0:22–0:30** | Cut to the athlete-facing view (default landing). Red alert: *"Your likeness has been misused"* · *"आपकी छवि का दुरुपयोग हुआ है"*. | "In 90 seconds, Aegis finds the deepfake, notifies the athlete, drafts jurisdiction-aware takedowns, and anchors a public audit receipt." | bilingual |
| **0:30–0:50** | Screen: a broadcaster dashboard. Drag-and-drop upload of the clean original. C2PA signing animation: keyframes extracted, pHash + embedding generated, C2PA manifest signed by Cloud KMS, "published" receipt shown. | "At publication, Aegis signs every clip with a cryptographic content credential and fingerprints it two ways — perceptual for scale, embedding for semantic robustness." | EN + HI |
| **0:50–1:10** | Cut to a fake third-party site. The manipulated clip appears (still watermarked `CONSTRUCTED TEST SCENARIO`). Timer ticking. Dashboard on the right shows the incoming `POST /detect`. | "Forty-five seconds later, a manipulated upload appears on a public platform. The crawler fetches the public URL — robots.txt-respected — and posts it to Aegis." | EN + HI |
| **1:10–1:30** | Dashboard displays the verdict appearing frame-by-frame: `verdict: DEEPFAKE_MANIPULATION · confidence: 0.94 · action: ATHLETE_ALERT_AND_TAKEDOWN`. Evidence list renders: temporal_face_flicker, lip_sync_drift, caption_assertion. | "Gemini verifies it's synthetic — despite adversarial transforms that defeat perceptual hashing. The verdict names the cues on screen." | EN + HI |
| **1:30–1:50** | Cut to athlete-facing view: red banner in Hindi + English. One-click to a takedown queue showing 4 platform agents. | "The athlete gets a bilingual alert. Not after review. Not the next day. Now." | EN + HI |
| **1:50–2:10** | Agents panel. Four cards update in parallel: X, YouTube, Meta, Telegram. Each shows its jurisdiction badge (US-DMCA §512(c), or IN-IT Rules 2021 + MeitY 2023). Notices draft, submit, and acknowledge; mock ticket IDs appear. | "Per-platform agents draft jurisdiction-aware takedowns. DMCA for US-hosted content. IT Rules 2021 and the MeitY 2023 synthetic-media advisory for India. Four platforms, one action." | EN + HI |
| **2:10–2:30** | Side-by-side of the DMCA and IT Rules notices. Key clauses highlighted: §512(c)(3) sworn statement on one side; Rule 3(2)(b) + 24-hour MeitY timeline on the other. | "Real notices — copy-paste-ready — populated by Gemini from the detection record. No template stuffing. No guesswork on statutes." | EN + HI |
| **2:30–2:40** | `/verify/{detection_id}` page loads. Merkle root, KMS key version, signature visible. Copy-link button. | "Every claim and every takedown is anchored into a daily Merkle root, signed by Cloud KMS. Anyone can verify a receipt." | EN + HI |
| **2:40–2:45** | Logo + team names + URL + SDG 5 + 16 badges. | "Aegis. For the people whose likenesses are at stake." | EN + HI |

**Total:** 2:45 exactly.

---

## Live-pitch fallback (if video does not play)

Run `python demo/seed_demo.py --original data/originals/clean.mp4 --leak data/case-study/generated/meera-deepfake.mp4 --api-base https://aegis-api.run.app` on a clean terminal with large font. The printed JSON walks the same pipeline; narrate it line-by-line for 90 seconds. See `deck/deck.md` slide 6 fallback note.

---

## Non-negotiables

- `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark visible on every frame that contains the manipulated clip. Cover frames with the watermark burned in at 100% opacity in the bottom-right.
- "Not real, no real person depicted" appears at least once on-screen during 0:08–0:15 as a title-safe overlay.
- Bilingual captions. Both languages present, both legible on 1080p.
- Cold open is athlete-harm. Piracy statistics (IPL volume, etc.) do NOT appear before the 0:30 mark. They can appear later if budget permits (slide 8 "Impact" uses them).

## What the video does not show

- No real athletes. Anywhere. At any point.
- No real league footage. Every clip on screen is CC-licensed or generated.
- No real platform takedown. The four platform cards explicitly say "mock endpoint" in small print.
- No personal contact information. Rights-holder contact in the DMCA / IT Rules notices uses `demo@aegis.test`.
