# Case-Study Sources — Test-Subject Meera persona

Every image, voice sample, and clip component used to construct the fictional "Test-Subject Meera" persona is listed below with its license and original source. No real athlete's likeness appears.

**Rule:** if it is not listed here with a CC-0 / CC-BY / public-domain attribution or a synthesis-log entry, it does not appear in the demo.

## Portraits / likeness composition

| Asset ID | Source | License | URL | Used where |
|---|---|---|---|---|
| `portrait-01.jpg` | *TBD — team PM to populate* | CC-0 / CC-BY / public domain | — | Base face image for the constructed persona |
| `portrait-02.jpg` | *TBD* | — | — | Secondary angle |
| `portrait-03.jpg` | *TBD* | — | — | Three-quarter angle |

## Voice samples (for lip-sync track)

| Asset ID | Source | License | URL | Used where |
|---|---|---|---|---|
| `voice-01.wav` | *TBD — CC-licensed speech dataset or team recording* | — | — | Base voice for the fictional persona |

## Stadium / match-context footage (clean originals)

| Asset ID | Source | License | URL | Used where |
|---|---|---|---|---|
| `match-clean-01.mp4` | Pro Kabaddi CC-licensed highlights *or* CC-BY cricket reel *or* team-generated Veo-3 footage | CC-BY / CC-0 / team-generated | — | The "clean original" published to Aegis at `POST /ingest` in the demo |

## Generated manipulated clip (the deepfake used in the demo)

See `data/case-study/generation-log.md` for the production log and `data/case-study/destruction-log.md` for the destruction confirmation (populated post-Phase-3).

## Citations used in the deck (not re-hosted)

| Reference | Citation | Why it's cited |
|---|---|---|
| 2023 Rashmika Mandanna deepfake incident | *TBD news sources at submission time* | Public-incident anchor for the harm pattern (deck slide 1 ticker) |
| MeitY advisory on synthetic media, Nov 2023 | *TBD MeitY / PIB press release URL* | Regulatory basis cited in `docs/why-not-drm.md` and in the IT Rules 2021 takedown template |
| Information Technology Rules 2021 (as amended 2023) | *TBD official gazette / meity.gov.in URL* | Legal basis for the India-jurisdiction takedown notices |
| DMCA 17 U.S.C. §512(c) | *TBD congress.gov / copyright.gov URL* | Legal basis for the US-jurisdiction takedown notices |

## Stock portrait search queries (for PM to work from)

When PM populates this file:
- "CC-0 woman portrait studio" on Unsplash, Pexels, Pixabay
- "public domain cricket portrait" on Flickr (filter: public domain) or Wikimedia Commons
- Prefer images labelled explicitly with a license ID (CC0-1.0, CC-BY-4.0). Screenshot the license badge and save it alongside the asset.

## License check at submission time

Before the demo video is uploaded:
- [ ] Every listed asset has a confirmed license, archived with the asset
- [ ] Every URL resolves (or has an archive.org snapshot fallback)
- [ ] The persona's name, league name, and match ID are all prefixed "Test-Subject" / "Test-League" per `docs/case-study.md`
- [ ] The `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark is burned into every frame that shows the manipulated clip
