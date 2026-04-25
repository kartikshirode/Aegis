# Generation Log — Constructed Test-Subject Meera Clip

This file is the ethics-defense record for the single manipulated clip produced for the Aegis flagship demo. Fill it in BEFORE recording the demo video; do not produce the clip without populating these fields.

## Purpose

- Scenario demonstration for the 2:45 demo video and the live-pitch fallback.
- Exercise the `DEEPFAKE_MANIPULATION` path of `backend/prompts/verdict.txt` with a controlled input.
- Produce the specific adversarial signal (lip-sync drift, face-region compression disparity) that the classifier cues document.

## Input assets

See `sources.md`. Composite inputs:
- Base portrait of the fictional persona — CC-licensed still (see `sources.md`)
- Clean talking-head footage — CC-licensed video (see `sources.md`)
- Synthesized voice track — generated offline using Windows SAPI System.Speech (no network, no commercial API)

## Production details

| Field | Value |
|---|---|
| Operator (team member) | *Kartik Shirode* |
| Date / time (UTC) | 2026-04-25T20:49:12Z |
| Machine (hostname, OS) | WIN-P969HU5QK25 · Windows 11 Home Single Language 10.0.26200 |
| Tooling | FaceFusion 3.6.1 (face_swapper + lip_syncer); ffmpeg 8.1; Windows SAPI System.Speech.Synthesis (built-in, offline TTS) |
| Tool versions | FaceFusion 3.6.1 (https://github.com/facefusion/facefusion); ffmpeg version 8.1-full_build (Gyan); Windows SAPI built into OS |
| Models | face-swapper: `hyperswap_1c_256` (pixel-boost 512×512); face-enhancer: `gfpgan_1.4` (blend 80); lip-syncer: `wav2lip_gan_96` |
| Execution provider | CUDA (onnxruntime-gpu 1.24.4 with CUDA 12.9 runtime + cuDNN 9.21 via nvidia-* pip wheels — DLL paths prepended to PATH at launch) |
| Hardware | NVIDIA GeForce RTX 4060 Laptop, 8GB VRAM (driver 581.80) — GPU pegged at 100% / 7.9 GB VRAM during the swap |
| Output video quality | CRF 18 (libx264, near-visually-lossless) |
| Input asset SHA-256s | face-source.jpg: `03e9e2410e88061cec6995f37ffa5a11761117339440f9c29917d2c131532e12` · face-target.mp4 (original 4K): `499a1104ca26b457810bd3d189798f9b1dff7ca38197b3dba462c5e4d7038608` · face-target-720p.mp4 (downscaled): `ca379db719082eead7980261688ebbf3b249a3e1ba98dc6f12f1d8cbe2fea539` · fake-audio.wav: `ef45b2a48ad723b520c983e39771270ca654191a6d1210de14f8cd049b984a34` |
| Intermediate output | `data/case-study/sources/swapped-raw-v2.mp4` (FaceFusion output before watermark/caption) — SHA-256: `8fe47dceebd854cc6d520b2e798f1dee0643342bba9377675acec3fa2bfe2a5c` |
| Output clip path (local) | `data/case-study/generated/constructed-meera-clip.mp4` |
| Output SHA-256 | `e85e31d50c1cb86c29afbee9a73c36bd0b25ab15f809b5368a2e7bd8afdec380` |
| Output size | 4,881,296 bytes (≈4.7 MB) |
| Watermark burned-in | `CONSTRUCTED TEST SCENARIO · NOT REAL` · bottom-right · 100% opacity · 48pt |
| Visibility of persona name on-screen | "Test-Subject Meera (fictional)" lower-third, full duration |
| Duration | 20 seconds (trimmed via ffmpeg `-t 20`) |
| Resolution | 1280×720 |
| Frame rate | 30 fps |

## Synthesis text (audio script)

The full script spoken by the synthesized voice, verbatim:

> "I am Test-Subject Meera, a fictional cricketer in a fictional Test-League. I am reading scripted text for the Aegis demonstration. This is not a real admission. This audio was synthesized for testing only."

Generated via `System.Speech.Synthesis.SpeechSynthesizer` (Windows built-in), default voice (Microsoft Zira), rate 0, output as 22 kHz 16-bit mono WAV.

## What the clip depicts

A fictional woman cricketer ("Test-Subject Meera") appearing to say, on camera, that she received a match-fix payment. The statement is wholly fabricated. The persona is wholly fictional. No real person makes or has ever made this statement.

## Distribution

- Stored on the operator's machine and the shared team drive; not uploaded to any public file host.
- Seeded at demo time on a controlled test domain we operate (e.g., `https://aegis-test-domain.example/`).
- Never posted to any real platform. Never shared with anyone outside the Aegis team.
- The original source video and source portrait are publicly licensed (see `sources.md`); the constructed clip itself is not redistributed.

## Destruction plan

See `destruction-log.md`. After Grand Finale (or after Phase 1 if the project does not progress), the operator destroys the generated clip and logs the destruction in `destruction-log.md` with the output SHA-256.

## What this clip is not

- Not a training input for the Aegis deepfake classifier — training uses DFDC and Celeb-DF only, see `docs/dataset-cards/`.
- Not a product feature — Aegis does not generate or host manipulated media as part of its runtime behaviour. See `docs/ethics.md` §"No generation path in the product".
- Not a deepfake of any real person. The persona is fictional, the league is fictional, the match is fictional.
- Not generated using any commercial or Google API — all synthesis is offline using open-source / built-in OS tooling.
