# Problem Statement — as Aegis scopes it

**Track:** PS#1, Digital Asset Protection — "Protecting the Integrity of Digital Sports Media"
**Challenge:** Google Solution Challenge 2026 · Build with AI

## What the brief asks

> *"Identify, track, and flag unauthorized use or misappropriation of official sports media across the internet. Enable organizations to proactively authenticate their digital assets and detect anomalies in content propagation in near real-time."*

## Why this is worth solving (the human-harm framing)

The default reading of this brief is "help leagues and broadcasters protect their content from pirates." That framing is incomplete, and it is the framing that every other submission will default to. Aegis re-anchors the problem around the two human-harm surfaces that the corporate-IP reading misses:

1. **Non-consensual synthetic media of athletes — especially women.** The 2023 deepfake incident targeting an Indian public figure catalyzed MeitY's advisory on synthetic media under the IT Rules 2021. The same pattern is extending to women athletes, who have public profiles, growing media value, and no media-industry piracy-defense budget.
2. **Misinformation in sport.** Fabricated match-fix "admissions," manipulated press-conference audio, and AI-generated "leaked" footage are live vectors of misinformation that move betting markets, damage reputations, and reach millions before any correction does. This is an integrity problem for the sport itself, not only for the rights-holder.

Piracy of league footage is real — and Aegis handles it — but it is the *downstream* harm. The *upstream* harms are athlete-harm and misinformation, and they are what a PS#1 submission in 2026 must centre.

## Why now

- **Gemini multimodal** makes frame-plus-audio semantic verdicts feasible at a quality that pHash-only approaches cannot reach — particularly against adversarial transforms.
- **C2PA** content credentials are now a ratified standard with reference implementations, so "signed at publication" is finally a shippable primitive rather than a research plan.
- **India IT Rules 2021** (as amended 2023) and MeitY's **November 2023 synthetic-media advisory** give Aegis a concrete legal hook for takedown notices specific to deepfakes of Indian persons — a jurisdictional substrate that did not cleanly exist three years ago.

## What Aegis delivers (Phase 1 scope — 24 Apr 2026)

- **Provenance at source** — C2PA-signed content credentials for official media.
- **Detection + Classification in the wild** — two-stage pipeline combining pHash / perceptual fingerprinting with Vertex AI multimodal embeddings and a Gemini 2.5 Pro verdict agent. Adversarially robust against re-encode, crop, mirror, AI-upscale, caption overlay.
- **Deepfake & likeness-abuse detection** — dedicated classifier and athlete alert surface, bilingual English / Hindi.
- **Agentic takedown pipeline** — per-platform notice drafting with Gemini, jurisdiction-aware (DMCA §512(c) for US-hosted content, IT Rules 2021 for India-hosted content), filed into mock platform endpoints for the demo.
- **Tamper-evident audit trail** — daily Merkle root, Cloud-KMS-signed, published on a public `/verify` endpoint.

## What Aegis deliberately does *not* deliver in Phase 1

- Real-platform takedown submission. We file to honeypot endpoints we control; production platform integration is Phase 2.
- Full-scale crawler coverage. Phase 1 shows a narrow vertical slice (≤ 4 mock domains); breadth is Phase 2.
- Fine-tuned deepfake classifier. Phase 1 uses Gemini 2.5 Pro zero-shot; the fine-tuned head is Phase 2.
- Federated fingerprint indexing. Phase 2 architectural beat, gestured at in the roadmap slide only.

## Beneficiary order (the framing decision that shapes everything else)

1. **Athletes**, especially women athletes whose likenesses are targets of non-consensual deepfakes. Default, unauthenticated landing page of the product.
2. **Sports fans**, who deserve to know which clip is real. Verify page is public and rate-limit-free.
3. **Rights-holders and publishers**, who benefit — but who are not the protagonists. Dashboard sits behind auth.

See [`docs/sdg-alignment.md`](sdg-alignment.md), [`docs/why-not-drm.md`](why-not-drm.md), [`docs/ethics.md`](ethics.md), [`docs/case-study.md`](case-study.md), and [`docs/benchmarks.md`](benchmarks.md) for the full framing.
