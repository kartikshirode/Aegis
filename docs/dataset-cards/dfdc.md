# Dataset Card — DFDC (Deepfake Detection Challenge)

**Source paper:** Dolhansky, B. et al. *The DeepFake Detection Challenge (DFDC) Dataset.* arXiv:2006.07397 (2020).
**Use in Aegis:** held-out evaluation set for the deepfake detection pillar. Phase 1 uses the deepfake rubric embedded in `backend/prompts/verdict.txt`; `backend/prompts/deepfake_verdict.txt` is a Phase-2 escalation prompt, ready but not yet wired. Fine-tuned classifier head is Phase 2.

## Composition

- ~100K video clips produced on behalf of the original DFDC by Facebook AI, with paid, consenting actors.
- Each clip is either a genuine recording of an actor or a manipulated version produced with one of several face-swap / synthesis methods.
- Released under a specific DFDC research-use license; redistribution terms apply.

## Why we use it

- It is the largest publicly available deepfake dataset with consented actor likenesses, making it the only honest choice for a student project that does not want to train on scraped content.
- It exposes the classifier to multiple generator architectures, which directly affects the out-of-distribution-generator AUROC target in `docs/benchmarks.md`.

## Where it lives

- Not committed to this repository. License and size preclude redistribution.
- Phase-1 teams fetch the subset per the DFDC license and store locally. In Phase 1 the data is consumed only for held-out benchmark eval of the deepfake rubric inside `verdict.txt` (zero-shot Gemini inference; no training). Phase 2 adds (a) the dedicated `deepfake_verdict.txt` escalation path and (b) a Vertex AI classifier fine-tune on top of it.

## Known limitations

- Post-2020 generator architectures (latent-diffusion-based face swap, for example) are not present; novel-generator performance is a known OOD degradation — published in `docs/benchmarks.md`.
- Recording conditions skew toward controlled indoor lighting; low-light cricket broadcast footage is an OOD axis we separately flag.
- Voice manipulation is only partially represented; audio-only cues (spectral flatness, prosody monotony) receive lower training signal than visual cues.

## Ethics notes (carried over from `docs/ethics.md`)

- Actors in DFDC consented. We do not extend their likeness beyond evaluation inside Aegis.
- We do not use DFDC to produce any demo artefact. The single constructed demo clip is produced separately; see `data/case-study/generation-log.md`.
