# Benchmarks — Aegis

Numbers, not claims. A submission that says *"we have benchmarks"* without specific targets caps around 28/40 on Technical Merit. This document specifies the metric, the target, and the evaluation protocol for each. Final numbers replace the Phase-1 targets column at submission time; any gap between target and actual is itself documented, not hidden.

## What Phase-1 honestly measures

The Phase-1 benchmark runs the variant corpus through the **currently configured thresholds** (`PHASH_ESCALATE_DISTANCE`, `EMBEDDING_ESCALATE_COSINE` in `backend/detect.py`). It does **not** sweep thresholds and does **not** produce a full ROC curve. Two numbers result:

- **match_rate** — fraction of variants where Stage 1 escalated to a Gemini verdict
- **recall** — fraction of variants where the retrieved `clip_id` is exactly the expected source clip's `clip_id` (i.e. we got the right clip, not just any clip). This is the number the deck should cite.

"Recall at ≤ 5% FPR" is the Phase-2 framing — it requires a labelled negatives corpus + threshold sweep, both of which are `benchmark/run.py --sweep` work we haven't done. The table below uses honest language.

## LOCAL-mode caveat

The mock embedding in LOCAL mode is similarity-preserving (derived from pHash bits) but it is **not a Vertex AI multimodal embedding**. Numbers produced with `AEGIS_INDEX_MODE=LOCAL` are a lower bound; real Vertex AI numbers are materially different. **Any benchmark number cited in the deck must come from a run with `VERTEX_AI_PROJECT` set.** `benchmark/run.py` prints the mode it was run in at the top of `summary.json` — judges can verify.

## Phase 1 (24 Apr 2026 submission) targets

| Metric | Phase-1 target | How it is measured |
|---|---|---|
| **Recall** (retrieved clip_id is the expected source clip) on single-transform variants | **≥ 0.80** | 30 CC-licensed originals × 5 single transforms (re-encode · crop · mirror · AI-upscale · caption overlay) = 150 pairs. See `benchmark/generate_variants.py`. Requires `VERTEX_AI_PROJECT` for honest numbers. |
| **Recall** on multi-transform chains | **≥ 0.65** | Reported separately. Subset of 50 pairs with 2–3 composed transforms. Degradation under composed attacks is expected and published. |
| **Match rate** (Stage-1 escalated to a verdict) | **≥ 0.90** single-transform · **≥ 0.75** multi-transform | Same corpora. Reported alongside Recall so the gap (match-rate minus recall) exposes retrieval-confusion cases. |
| Precision@5 for Vector-Search retrieval | **≥ 0.80** | 50-query eval set; labelled relevant matches from the 150-variant corpus. |
| Deepfake verdict agreement with ground truth | **≥ 0.80** (accuracy) | Zero-shot Gemini 2.5 Pro classification on a 30-clip labelled set (15 genuine + 15 DFDC samples). No fine-tune in Phase 1 — this is explicitly the Phase-1 deepfake pillar. |
| End-to-end latency (detection → Gemini verdict → DMCA draft) | **< 90 s p95** | Measured across 20 consecutive demo-scenario runs. Headline number in the deck. |
| Pipeline integrity (classified match → correctly-formatted, filed, logged notice) | **100%** | Integration test: for every match classified at or above takedown threshold, verify a platform-specific notice is generated to spec, submitted to the configured mock endpoint, and a receipt is persisted in the audit log. **Measures our pipeline, not the platforms.** |
| False-positive rate on fair-use commentary set | **≤ 10%** | 30 CC-licensed commentary / reaction clips. Phase-1 target is loose; tightens in Phase 2 when the threshold sweep lands. |

## Grand Finale targets (if Top 100 → Top 10)

| Metric | Finale target |
|---|---|
| Recall on single-transform at ≤ 5% FPR (threshold sweep lands in Phase 2) | **≥ 0.90** |
| Recall on multi-transform chains at ≤ 5% FPR | **≥ 0.80** |
| Precision@5 | **≥ 0.90** |
| Deepfake detection AUROC (DFDC held-out) with Phase-2 fine-tuned head | **≥ 0.90** |
| Deepfake detection AUROC on novel-generator OOD set | **≥ 0.75** · published even if lower |
| End-to-end latency | **< 60 s p95** at 100K-item index |
| Crawler throughput | **≥ 1,500 URLs/min** |
| Pipeline integrity | **100%** maintained across full-platform agent set |
| False-positive rate on fair-use commentary | **≤ 2%** |

## Protocol notes

- **Every metric is reproducible.** Scripts live in `benchmark/`; the exact command to regenerate each number is in the doc header of each script.
- **The adversarial variant corpus is reproducible from seed.** `benchmark/generate_variants.py` is deterministic given a fixed random seed; the seed is committed.
- **Labels are reviewed by two team members** before a metric is finalized. Disagreements are recorded.
- **If a Phase-1 target is missed,** the actual number is reported in its place alongside a one-line postmortem in `docs/benchmark-postmortem.md`. Missing a target is acceptable; hiding the miss is not.

## What the pipeline-integrity metric is, and is not

- It is **not** "did the platform accept our takedown." We cannot measure that against real platforms within the ethics boundary of this project.
- It is: *given a classified match at or above threshold, did the notice get correctly generated (platform-specific template, required fields populated, jurisdictional basis correct), submitted to the configured endpoint, and a structured receipt logged?*
- The mock endpoints are structured to return the exact shape of real platform responses (success / malformed / rate-limited / auth-failed) so the pipeline is exercised against realistic conditions.
- This is why the metric can legitimately read 100%: it measures **our pipeline**, which we fully control and test. It would be meaningless to claim 100% against platforms we do not control.

## Known failure modes (published deliberately)

- **Low-light footage** — perceptual hashing degrades below ~25 lux equivalent; embedding quality also drops. Documented; no Phase-1 mitigation planned.
- **Novel generator architectures** (generators released after our training cutoff) — detection quality falls sharply. Mitigation roadmap: periodic retraining in Phase 2, with dataset deltas published.
- **Very short clips (< 2s)** — scene-hash coverage is insufficient for reliable recall. Demo scenarios use clips ≥ 10s.
- **Speed-shifted clips (>1.5× or <0.66×)** — audio track disagreement confuses the classifier. Single-axis speed up to 1.25× is handled.
- **Multi-language captions / overlays** — large caption overlays reduce embedding similarity below threshold in ~15% of cases; flagged in the red-team report.
