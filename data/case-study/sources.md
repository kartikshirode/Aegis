# Case-Study Sources — Test-Subject Meera persona

Every image, voice sample, and clip component used to construct the fictional "Test-Subject Meera" persona is listed below with its license and original source. No real athlete's likeness appears.

**Rule:** if it is not listed here with a CC-0 / CC-BY / public-domain attribution or a synthesis-log entry, it does not appear in the demo.

## Portraits / likeness composition

| Asset ID | File | Source (URL) | License | Author / Credit | Used where |
|---|---|---|---|---|---|
| `face-source.jpg` | `data/case-study/sources/face-source.jpg` | *https://unsplash.com/photos/young-woman-in-white-dress-holding-lilies-lu5IbAS4mxg* | *https://unsplash.com/photos/young-woman-in-white-dress-holding-lilies-lu5IbAS4mxg* | *https://unsplash.com/photos/young-woman-in-white-dress-holding-lilies-lu5IbAS4mxg* | Source face for FaceFusion `face_swapper` |

License screenshot: `data/case-study/sources/face-source-license.png` *(MISSING — capture before submission)*

SHA-256: `03e9e2410e88061cec6995f37ffa5a11761117339440f9c29917d2c131532e12`

## Voice samples (for lip-sync track)

| Asset ID | File | Source | License | Used where |
|---|---|---|---|---|
| `fake-audio.wav` | `data/case-study/sources/fake-audio.wav` | Synthesized offline via Windows SAPI (`System.Speech.Synthesis.SpeechSynthesizer`, voice: Microsoft Zira) | OS-built-in synthesis, no third-party license required | Lip-sync audio track for FaceFusion `lip_syncer` |

Script: see `generation-log.md` § "Synthesis text (audio script)".

SHA-256: `ef45b2a48ad723b520c983e39771270ca654191a6d1210de14f8cd049b984a34`

## Stadium / match-context footage (clean target)

| Asset ID | File | Source (URL) | License | Author / Credit | Used where |
|---|---|---|---|---|---|
| `face-target.mp4` | `data/case-study/sources/face-target.mp4` | *https://www.pexels.com/video/woman-talking-while-drinking-her-coffee-6785643/* | *https://www.pexels.com/license/* | *https://www.pexels.com/@marcus-aurelius/* | Target video — speaker whose face is swapped and lips re-synced |

License screenshot: `data/case-study/sources/face-target-license.png` *(MISSING — capture before submission)*

SHA-256 (original 4K): `499a1104ca26b457810bd3d189798f9b1dff7ca38197b3dba462c5e4d7038608`
SHA-256 (downscaled 720p, used as actual swap input): `ca379db719082eead7980261688ebbf3b249a3e1ba98dc6f12f1d8cbe2fea539`

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
- [ ] License screenshots `face-source-license.png` and `face-target-license.png` exist in `data/case-study/sources/`
- [ ] Every URL resolves (or has an archive.org snapshot fallback)
- [ ] The persona's name, league name, and match ID are all prefixed "Test-Subject" / "Test-League" per `docs/case-study.md`
- [ ] The `CONSTRUCTED TEST SCENARIO · NOT REAL` watermark is burned into every frame that shows the manipulated clip
