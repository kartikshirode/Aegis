# Demo Cold-Open — replaces first 30 seconds of aegis-build-plan.md §8

The existing demo storyboard in `aegis-build-plan.md` Section 8 opens with *"Every minute, 12,000 pirated sports clips are uploaded to the open web."* This anchors judges on **corporate piracy** in the first sentence — exactly the framing that caps the 25% "Alignment with Cause" slice. This document replaces beats 0:00–0:30 of that storyboard; beats 0:30 onward remain as written.

## Revised beats 0:00–0:30

| Time | Shot | Narration |
|---|---|---|
| 0:00–0:08 | Dark frame. Text appears one word at a time in white: *"A video circulates of a woman athlete making a match-fix admission."* Single slow Hindi transliteration appears underneath: *एक महिला खिलाड़ी का वीडियो फैल रहा है.* | (silence on the video; only the words) |
| 0:08–0:15 | Cut to split screen — left side: the video clip (watermarked `CONSTRUCTED TEST SCENARIO · NOT REAL`); right side: a news-ticker animation of already-public reporting on the 2023 Rashmika Mandanna incident with citation line. | *"It's a deepfake. She never said it. The clip is already across four platforms before anyone notices."* |
| 0:15–0:22 | Title card: **Aegis**. Subtitle: *"Cryptographic provenance, deepfake defense, and agentic takedown — for the people whose likenesses are at stake."* | *"Aegis is an authenticity layer for sport — built for the athletes and fans, not the leagues."* |
| 0:22–0:30 | Quick cut to the athlete-facing view: Hindi + English alert. *"Your likeness has been misused."* | *"In 90 seconds, Aegis finds the deepfake, notifies the athlete, drafts jurisdiction-aware takedowns, and anchors a public audit receipt."* |

## Opening thirty-second script (read by voiceover)

> *"A video circulates of a woman athlete making a match-fix admission. It's a deepfake. She never said it. The clip is already across four platforms before anyone notices. Aegis is an authenticity layer for sport — built for the athletes and fans, not the leagues. In 90 seconds, Aegis finds the deepfake, notifies the athlete, drafts jurisdiction-aware takedowns, and anchors a public audit receipt."*

## Why this opener

- **First-sentence anchor is human harm**, not a piracy volume statistic. The IPL-40-million number still appears later in the deck as a scale stat, but not in the first breath of the video.
- **Names the beneficiary class** in the first 22 seconds: "athletes and fans, not the leagues." Pre-empts the DRM dismissal before it can form.
- **Credits the Indian context** via the Rashmika Mandanna public-incident reference. Tells Indian judges we understand the reality they see in their news feeds.
- **Sets up the rest of the video** to execute the athlete-first demo storyline from `docs/case-study.md`.

## What must stay unchanged from the original storyboard

Beats 0:30–2:45 of the original `aegis-build-plan.md` Section 8 are substantially correct and stay. Key adjustments bolted on:

- **Beat 0:50–1:30** — when the dashboard lights up with a new detection, the first dashboard view shown is the **athlete-facing view in Hindi + English**, not the rights-holder dashboard. The rights-holder view is shown for 3–5 seconds later as a secondary surface.
- **Beat 2:00–2:20** — DMCA draft animation is extended to show both an **IT Rules 2021** notice (India-hosted target) and a **DMCA §512(c)** notice (US-hosted target) side by side. Demonstrates the jurisdiction-aware logic judges will ask about.
- **Beat 2:20–2:40** — keep SportSig-Bench mention, but immediately after show the `/verify` page displaying the Merkle-anchored receipt of one of the takedowns just filed in the demo. The trust-layer closing beat is what distinguishes us from "another piracy dashboard."

## Captions

All captions in the video are bilingual — English top, Devanagari Hindi below. This is not cosmetic: it is the SDG 5 / SDG 16 / SDG 8 framing made visible on screen.

## Total runtime after changes

Target stays at **2:45** on the nose. The cold open is shorter than the original (22 seconds narration vs 30 seconds), reclaiming ~8 seconds that go into the jurisdiction-aware takedown side-by-side at 2:00–2:20.

## Pre-flight before recording

Do this **once**, immediately before hitting Record. It takes 10 seconds and prevents the worst outcome: recording the demo against LOCAL mocks without realising.

```
curl $API_URL/demo/status
```

Confirm the response shows:
- `"index_mode": "GCP"` (not `LOCAL`)
- `"storage_mode": "GCP"`
- `"kms_mode": "GCP"`
- `"gemini_live": true`
- `"vector_search_configured": true`
- `"mock_endpoints"` — all four set to `true`

If any line says `"LOCAL"` or `false`, stop and fix the env on the Cloud Run revision. Recording a demo against LOCAL mocks produces numbers that are not real and a flow that slightly misbehaves — both will cost you credibility when judges retry the public URL.
