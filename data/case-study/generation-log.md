# Generation Log — Constructed Test-Subject Meera Clip

This file is the ethics-defense record for the single manipulated clip produced for the Aegis flagship demo. Fill it in BEFORE recording the demo video; do not produce the clip without populating these fields.

## Purpose

- Scenario demonstration for the 2:45 demo video and the live-pitch fallback.
- Exercise the `DEEPFAKE_MANIPULATION` path of `backend/prompts/verdict.txt` with a controlled input.
- Produce the specific adversarial signal (lip-sync drift, face-region compression disparity) that the classifier cues document.

## Input assets

See `sources.md`. Composite inputs:
- Base portrait(s) of the fictional persona (CC-0 / CC-BY portraits)
- Clean match footage (CC-licensed or team-generated)
- A voice sample (CC-licensed speech or team recording)

## Production details (populate before production)

| Field | Value |
|---|---|
| Operator (team member) | *TBD* |
| Date / time (UTC) | *TBD* |
| Machine (hostname, OS) | *TBD* |
| Tooling | *TBD — DFDC-adjacent open-source tooling, run offline; no commercial / Google API used* |
| Tool versions | *TBD* |
| Input asset SHA-256s | *TBD (one hash per input)* |
| Output clip path (local) | `data/case-study/generated/constructed-meera-clip.mp4` |
| Output SHA-256 | *TBD — filled after production* |
| Watermark burned-in | `CONSTRUCTED TEST SCENARIO · NOT REAL` · bottom-right · 100% opacity · 48pt |
| Visibility of persona name on-screen | "Test-Subject Meera (fictional)" lower-third, full duration |
| Duration | ~20 seconds |
| Resolution | 1280×720 |
| Frame rate | 30 fps |

## What the clip depicts

A fictional woman cricketer ("Test-Subject Meera") appearing to say, on camera, that she received a match-fix payment. The statement is wholly fabricated. The persona is wholly fictional. No real person makes or has ever made this statement.

## Distribution

- Stored on the operator's machine and the shared team drive; not uploaded to any public file host.
- Seeded at demo time on a controlled test domain we operate (e.g., `https://aegis-test-domain.example/`).
- Never posted to any real platform. Never shared with anyone outside the Aegis team.

## Destruction plan

See `destruction-log.md`. After Grand Finale (or after Phase 1 if the project does not progress), the operator destroys the generated clip and logs the destruction in `destruction-log.md` with the output SHA-256.

## What this clip is not

- Not a training input for the Aegis deepfake classifier — training uses DFDC and Celeb-DF only, see `docs/dataset-cards/`.
- Not a product feature — Aegis does not generate or host manipulated media as part of its runtime behaviour. See `docs/ethics.md` §"No generation path in the product".
- Not a deepfake of any real person. The persona is fictional, the league is fictional, the match is fictional.
