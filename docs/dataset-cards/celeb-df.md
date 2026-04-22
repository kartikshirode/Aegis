# Dataset Card — Celeb-DF v2

**Source paper:** Li, Y. et al. *Celeb-DF: A Large-scale Challenging Dataset for DeepFake Forensics.* CVPR 2020.
**Use in Aegis:** complementary deepfake evaluation set with subjects drawn from publicly available interviews of public figures, plus a matched set of synthesis artefacts.

## Composition

- ~5,600 clips: 590 originals (YouTube interviews of 59 celebrities) and ~5,000 deepfakes produced by the dataset authors.
- Deepfakes span varied lighting, compression, and motion conditions — a better proxy for sport-broadcast conditions than early DFDC.

## Why we use it (alongside DFDC)

- DFDC's studio-controlled lighting is not representative of match footage. Celeb-DF covers more "wild" conditions.
- It is our primary check for the classifier's robustness to lighting and compression drift.

## Where it lives

- Not committed to this repository. Research-use license terms apply.
- Used for held-out evaluation only in Phase 1; optionally augments fine-tune data in Phase 2.

## Known limitations

- The originals are sourced from public interviews of real people. Aegis does not extend or publish any likeness from Celeb-DF beyond internal evaluation metrics.
- Sports-specific motion (fast pans, rapid player motion, occlusions) is under-represented. The team's Phase-2 plan adds a small sports-specific adversarial set.

## Ethics notes

- The original subjects are public figures whose interviews are already in the public domain of reporting. We still do not produce any new synthetic media of any real person using this dataset.
- Evaluation numbers attributed to Celeb-DF are reported in aggregate on `docs/benchmarks.md` — never per subject.
