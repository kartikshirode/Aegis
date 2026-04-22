# Ethics Statement — Aegis

Aegis works in a domain where the same techniques that detect abuse can enable it. This document describes the guardrails that make the project defensible, and the behaviors we commit to.

## Training-data provenance

- **Deepfake classifier training sets:** **DFDC** (Deepfake Detection Challenge) and **Celeb-DF** only, both public research datasets. Dataset cards from the original papers are reproduced in `docs/dataset-cards/` (Phase 2 — sources cited inline for Phase 1).
- **Sports-media corpus:** only Creative-Commons-licensed or explicitly-permissively-licensed footage. Sources include Pro Kabaddi highlight packages under permissive terms, YouTube CC-filtered cricket clips, and MIT-licensed open sports datasets. For unambiguous ownership, a portion of the demo corpus is AI-generated sports footage produced by the team.
- **No scraping of copyrighted footage for any purpose** — training, evaluation, demo, or illustration. This is non-negotiable. If we cannot source something under a permissive license, we do not use it.
- **No private athlete imagery.** We do not train on, index, or demo real athlete likenesses outside the boundary of published public-incident reporting. Any public-incident reference (e.g., the 2023 Rashmika Mandanna deepfake) is *cited*, not rehosted or regenerated.

## No generation path in the product

Aegis detects and reports. It does not generate manipulated media. There is no endpoint, agent action, or UI affordance that produces deepfakes, face-swaps, or synthetic voice.

The one exception is a single demo artifact: one manipulated clip of a fictional persona ("Test-Subject Meera") used to walk judges through the flagship scenario. This clip is produced offline on a developer machine, is labelled "Constructed test scenario" on every demo frame, is never exposed via a product surface, and is destroyed after Phase 3. See `docs/case-study.md` for the full scenario specification.

## Takedown restraint

- Agents file platform-specific takedowns **only** for content classified as `verbatim_piracy` or `deepfake_manipulation` at or above the published confidence thresholds.
- All other classes (`edited_highlight`, `fair_use_commentary`, `screen_recording`, `false_positive`) route to a human-review queue. No auto-filing.
- Thresholds and their rationale are published in `docs/benchmarks.md` and in the live `/benchmarks` page on the MVP.
- A rights-holder or affected individual must be associated with any filed notice. Aegis does not file on its own behalf.

## Opt-in athlete enrollment

- The athlete-facing view requires explicit sign-up by the athlete (or an authorized representative).
- We do not build likeness profiles, reverse-image-search dossiers, or embedding galleries for athletes who have not enrolled.
- An enrolled athlete can revoke their enrollment at any time; the revoke flow deletes the likeness embedding and disables further alerts.

## Legally defensible crawling

- Publicly reachable URLs only. No authentication bypass, no credential reuse, no paywall circumvention.
- `robots.txt` is respected. Rate limits are conservative; we do not stress-test platforms we do not own.
- Platform ToS are not systematically circumvented. Where a platform ToS prohibits automated access, we rely on that platform's published API or do not crawl it.
- Aegis's role is **observability + notice-generation** for rights-holders and affected individuals who possess enforcement authority under the applicable jurisdiction (India IT Rules 2021 / US DMCA §512(c), see `docs/why-not-drm.md`). Aegis does not enforce on its own.

## Failure-mode disclosure

- The classifier has known failure modes. They are published, not hidden:
  - Low-light footage degrades both perceptual hashing and multimodal embedding quality.
  - Novel generator architectures released after our training cutoff will produce adversarial examples we currently mis-classify. AUROC numbers on a held-out novel-generator set are reported alongside the primary numbers even if they are low.
  - Heavy multi-transform chains (mirror + crop + re-encode + speed-shift + overlay) degrade recall below single-transform numbers.
- Judges and users should read `docs/benchmarks.md` alongside this document.

## Dual-use considerations

The same fingerprint and embedding pipeline that finds stolen clips could, in principle, be used to track public commentary or fan-made derivatives. Aegis mitigates this through:

- **Classification gates.** Fair-use commentary is a labelled class and is explicitly excluded from takedown actions.
- **Threshold transparency.** The exact confidence thresholds and classification boundaries are published.
- **Rights-holder scope.** An enrolled rights-holder can only monitor content they have published through Aegis's provenance layer. They cannot retroactively monitor arbitrary third-party content.

## What we will not do — even if asked

- Build a surveillance tool for individuals who have not opted in.
- Use Aegis to silence legitimate commentary, criticism, or parody.
- Generate or assist in generating deepfake content.
- Offer any feature whose primary use is the suppression of fan-made derivatives that qualify as fair use.

## Contact

Concerns, disclosures, and failure-mode reports can be filed via the public GitHub issue tracker for the duration of Phase 1. A dedicated security / ethics contact is added in Phase 2 if the project progresses.
