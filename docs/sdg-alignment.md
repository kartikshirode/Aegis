# SDG Alignment — Aegis

## Primary SDGs

### SDG 5 — Gender Equality
Non-consensual deepfakes disproportionately target women. India's 2023 advisory on synthetic media under the IT Rules 2021 was catalyzed by a deepfake targeting a prominent Indian public figure; the same pattern is increasingly targeting women athletes and sports broadcasters who have public-facing profiles but no media-industry piracy-defense budget.

Aegis's contribution:
- Deepfake / likeness-abuse detection is a first-class pillar, not a side feature.
- The athlete-facing view — Hindi + English — is the default landing page. Rights-holder dashboard is behind auth. This UX decision is the SDG-5 story made visible.
- Opt-in likeness enrollment; no dossiers on athletes who have not signed up.

### SDG 16 — Peace, Justice, and Strong Institutions
Fabricated sports clips (fake match-fix admissions, manipulated press conferences, AI-generated "leaked" footage) are vectors of misinformation. The 2024–2026 window has already produced multiple incidents of fabricated audio attributed to athletes and coaches that moved betting markets and damaged reputations before any correction reached the public.

Aegis's contribution:
- C2PA-compliant content credentials at publication provide a cryptographic answer to *"is this clip real?"* that any downstream consumer can verify.
- Tamper-evident audit trail (daily Merkle root signed via Cloud KMS) published on a `/verify` page gives the trust-layer its own public record.
- Classification pipeline distinguishes `deepfake_manipulation` from `verbatim_piracy` and routes deepfakes to priority takedown with athlete alert.

## Secondary SDGs

### SDG 8 — Decent Work and Economic Growth
Piracy and likeness theft directly attack the livelihoods of athletes, commentators, and independent creators — especially in regional and women's leagues that lack the budget for commercial Content-ID-grade defense. Aegis's permissively-licensed core is designed to be usable by a state kabaddi league or a women's hockey body without a commercial license.

### SDG 9 — Industry, Innovation, and Infrastructure
Aegis is infrastructure for trustworthy sports media: provenance + detection + audit in one open stack. This is the baseline innovation angle that PS#1 explicitly names; it is secondary because a PS#1 entry that anchors only on SDG 9 has historically not won.

## What is deliberately not claimed

- Aegis does not claim to solve gender-based violence, only one specific vector (image-based abuse via deepfakes of women athletes).
- Aegis does not claim to eliminate sports piracy, only to reduce time-to-takedown for notice-eligible content from days to minutes.
- We do not claim SDG 4 (Education), SDG 10 (Reduced Inequalities), or SDG 17 (Partnerships) because our evidence chain for those is weak. Claiming too many SDGs dilutes the primary story.

## How this is enforced in the submission

- **Demo cold open** leads with an athlete-harm moment, not a league logo. See `docs/demo-cold-open.md`.
- **README top-fold** states the primary beneficiary class as "athletes and fans."
- **Deck slide #1** is the hook; slide #2 is "What this is NOT" (DRM preempt, see `docs/why-not-drm.md`); slide #3 is SDG alignment with 5+16 in the primary tier and 8+9 in a visibly smaller tier.
- **Flagship demo scenario** is a deepfake of a fictional woman athlete, not a corporate piracy scenario. See `docs/case-study.md`.
