# Aegis is not DRM

This document pre-empts the most common dismissal of PS#1 solutions: *"isn't this just corporate DRM?"* It is linked from the README and is required reading before the demo.

## One-sentence answer

DRM restricts *who can play* official content. **Aegis attests *what content is real*** — and it is opt-in for the athletes and publishers who benefit from it, useless against paying consumers, and powerless without a rights-holder or an affected individual to file the notice.

## The contrast table

| | Traditional DRM | Content Credentials (C2PA) | **Aegis** |
|---|---|---|---|
| Restricts playback on licensed devices? | Yes | No | No |
| Attests origin / authenticity? | No | Yes | **Yes (uses C2PA)** |
| Detects unauthorized re-uploads in the wild? | No | No | **Yes** |
| Detects AI-manipulated / deepfake likenesses? | No | No | **Yes** |
| Drafts and files platform-specific takedowns? | No | No | **Yes (agentic)** |
| Opt-in for the athlete? | N/A | N/A | **Yes** |
| Primary beneficiary | Rights-holders | Publishers + consumers | **Athletes and fans** |
| Useless against? | Pirates | Unchanged pirates | Paying consumers (by design) |

## Who the product is for (in order)

1. **Athletes** — especially women athletes whose likenesses are targets of non-consensual deepfakes. Default landing page, Hindi + English.
2. **Sports fans** — who deserve to know which clip of their favorite player is real.
3. **Publishers and rights-holders** — who benefit, but who are not the protagonists. The rights-holder dashboard is behind auth so judges clicking around the MVP see the athlete view first.

## What Aegis does *not* do

- Does not prevent playback or copying of content. No DRM hooks, no device restrictions, no licensing server.
- Does not scrape or index copyrighted footage. Crawling is limited to public URLs, respects `robots.txt`, and no auth bypass.
- Does not file takedowns without a classification above the configured threshold. Everything below threshold goes to a human-review queue.
- Does not maintain likeness dossiers on athletes who have not enrolled. Athlete view is opt-in.
- Does not generate manipulated media. Detection and reporting only. The single generated asset used for the demo scenario is produced offline and destroyed post-demo.

## Jurisdictional basis for takedowns

Aegis is an **observability + notice-generation** tool. Enforcement authority rests with the rights-holder or the affected individual who files the notice — not with Aegis.

- **India-hosted content:** notices are formatted under the **Information Technology (Intermediary Guidelines and Digital Media Ethics Code) Rules, 2021**, which require intermediaries to act on takedown notices from affected individuals or authorized representatives within defined timelines. The 2023 IT Rules advisory on synthetic media further obliges intermediaries to remove morphed / AI-generated content on notification.
- **US-hosted content:** notices are formatted under **17 U.S.C. §512(c)** (DMCA safe harbor), including the sworn statement, good-faith belief clause, and rights-holder contact slots required for a valid notice.
- **Cross-border content:** Aegis identifies the hosting jurisdiction from the platform / domain and routes to the appropriate template. The agent module for each platform encodes its platform-specific submission protocol on top of the jurisdictional template.

## Licensing posture

- **Core provenance + athlete view + detection pipeline:** permissively licensed (Apache 2.0 or MIT). This is the free-to-use infrastructure that makes the SDG-5/16 story credible.
- **Commercial add-ons (Phase 2+):** premium rights-holder dashboard features, federated fingerprint indices, and SLA-backed hosting are the commercial surface. The free core is load-bearing; if a future pivot removed it, Aegis becomes DRM and this document stops being true.

## Why this framing matters for judging

The Solution Challenge's 25% "Alignment with Cause" slice historically favors human-impact SDGs. A PS#1 entry that anchors judges on corporate IP protection in the first 30 seconds of the pitch caps itself at ~60% on that slice. This document, the README top-fold, slide #2 of the deck, and the demo cold open are the four surfaces that jointly enforce the athlete-protection framing.
