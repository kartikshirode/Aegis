# Aegis Audit — v2

Fresh pass against v2 of the codebase, diffed against v1 and the v1 audit. Organised as: what got fixed, what's still broken (from v1), and what's new in v2.

---

## Summary

v2 is a substantially cleaner codebase than v1. The Claude Code implementer absorbed roughly **40 of the 50 v1 findings** and fixed them with care — not just patching the symptom, but picking the better design where there was one (e.g., the mock-embedding fix is a similarity-preserving pHash/dHash construction rather than a dependency swap). The highest-risk v1 findings (broken mock embeddings, benchmark that didn't measure recall, operator-precedence bug in mocks, Merkle race condition, swallow-everything exception handlers) are all properly addressed.

Residual issues are smaller in number and smaller in risk. One real bug (Candidate never persisted) still breaks the `/takedown` flow. A handful of dead-code / minor polish items remain. The brand-consistency call (Aegis vs Pramāṇ) was not taken — this is a product decision, not a bug.

**Verdict: Ship-ready after fixing one bug (unsaved Candidate) and deciding the brand question.**

---

## v1 findings that are now fixed

| # | Finding | Status | How |
|---|---|---|---|
| 1 | `HttpUrl` on `c2pa_manifest_url` rejects `file://` | **FIXED** | Field changed to `str` with explanatory comment |
| 2 | Same on `Candidate.url` and `TakedownNotice.target_url` | **FIXED** | Same pattern |
| 5 | Operator-precedence bug in mock platform SLA | **FIXED** | Extracted `is_synthetic_signal` variable with parens |
| 6 | `callable` used as type hint | **FIXED** | Proper `Callable[[str], Clip \| None]` from typing |
| 7 | `_PENDING` race condition | **FIXED** | `threading.Lock` with drain-outside-lock pattern; comment explains why asyncio.Lock isn't needed |
| 8 | `get_clip_video` raises `KeyError` | **FIXED** | Returns `Path \| None`; detect.py tolerates None |
| 9 | Double embedding in `/ingest` | **FIXED** | `ingest()` now returns `(Clip, embeddings)` tuple |
| 10 | robots.txt over-aggressive disallow | **FIXED** | RFC 9309 §2.3 compliant — 404/network-error = allow, 5xx/4xx-auth = deny |
| 11 | `takedown.py` swallow-everything excepts | **FIXED** | All four helper functions now propagate errors |
| 12 | Benchmark "recall" was actually match-rate | **FIXED** | Properly separated; `source_to_clip` map persisted; real `recall` metric defined |
| 13 | Gemini `Part.from_data` bytes size limits | **PARTIALLY FIXED** | Default is candidate-only (halves bytes); pair inclusion gated on ambiguity heuristic. Still no chunked/GCS-URI path for clips > 7MB — acceptable for Phase 1 demo clips |
| 14 | Both videos sent to Gemini on every call | **FIXED** | `_should_include_original` heuristic; only pair-verdict when signals are ambiguous |
| 15 | Dead heuristic path in `pick_jurisdiction` | **FIXED** | Single-line delegation to agent |
| 17 | Best-match ranker biased toward pHash | **FIXED** | Combined weighted score (0.7 embedding + 0.3 pHash); `_score` helper |
| 18 | Mock embedding not similarity-preserving | **FIXED (cleverly)** | pHash+dHash bit-vector with tile-to-dim; cosine sim tracks Hamming distance. Best fix in v2. |
| 20 | Deepfake pillar barely present | **FIXED (docs)** | README, benchmarks, case-study all now honestly say "Gemini zero-shot for Phase 1, classifier is Phase 2" |
| 26 | Caption-keyword rule in mock verdict leaks to production | **FIXED** | Gated behind `AEGIS_DEMO_MODE` env var; documented with reasoning |
| 27 | No way to confirm GCP vs LOCAL mode | **FIXED** | `/demo/status` endpoint reports all mode flags + live-credential presence |
| 29 | No threshold sweep in benchmark | **DOCUMENTED** | benchmarks.md now explicitly says "Phase 1 = fixed thresholds, sweep is Phase 2" instead of claiming an unsupported number |
| 31 | Footer doc links 404 on Firebase | **FIXED** | `VITE_AEGIS_DOCS_BASE` env with GitHub default; `target="_blank"` |
| 36 | "See drafted takedowns" dead button | **FIXED** | Now a `<Link>` to `/verify/{alertId}` |
| 37 | No path from alert → verify | **FIXED** | Same Link |
| 38 | `test_below_threshold_does_not_file` was a no-op | **FIXED** | Now uses `smptebars` vs `testsrc` — genuinely unrelated clips; asserts `matched=false` |
| 39 | Env-var leak in test | **FIXED** | All tests use `monkeypatch.setenv` |
| 40 | `setdefault` in conftest leaks developer's GCP env | **FIXED** | Autouse function-scope fixture with `monkeypatch.setenv` (override) + `delenv` for credentials + demo-mode |
| 41 | Loose verdict tuple assertion | **FIXED** | Tightened to `== "EXACT_PIRACY"`; separate deepfake test added |
| 42 | Crawler image never built | **FIXED** | `gcloud run jobs deploy --source ./services/crawler` |
| 43 | deploy.sh claims "one-shot" but VSC is manual | **FIXED** | Top-of-file note; renamed claim from "one-shot" to "mostly one-shot" |
| 44 | Env-vars comma-join broken on URLs with `,` | **FIXED** | Custom `^\|^` delimiter per gcloud convention |
| 46 | Ethics doc claimed watermark-stripping in dashboard | **FIXED (important)** | Now explicit: watermark is **never** removed, on any surface. Paragraph reframes the choice as deliberate. |
| 47 | Dataset cards said "Phase 2" despite existing | **FIXED** | Link to existing dfdc.md / celeb-df.md |
| 48 | README repo map missed `benchmark/run.py` | **FIXED** |  |
| 49 | README overclaimed deepfake classifier | **FIXED** | Honest downgrade; names the Phase-2 fine-tune |
| 50 | Architecture.md didn't reflect ADK fallback | **FIXED** | New "Multi-agent orchestration — what we shipped vs. what the plan described" section |

Fix quality is high. Most fixes add an explanatory comment or a paragraph explaining *why* — that's future-maintainer discipline.

---

## v1 findings still open in v2

### Real bugs
- **(v1 #16 — Candidate never persisted — still broken.)** `backend/main.py:detect_route` calls `store.put_verdict(verdict)` after detection but **never calls `store.put_candidate(candidate)`**. The Candidate object is constructed deep inside `backend/detect.py:detect()` (line 308-321 of v2), returned implicitly via the VerdictRecord that references its `candidate_id`, then discarded. When `/takedown` runs, it tries `store.get_candidate(verdict.candidate_id)` (main.py:199) and gets `None`, raising **404 "clip or candidate not found for detection"**. The entire demo flow dies here. This appears to have been present in v1 too and I missed it — apologies. **Ship-blocker.** Fix: either (a) return the Candidate from `detect.detect()` alongside the verdict and persist it in `main.detect_route`, or (b) move `put_candidate` inside `detect.detect()` via a callback param. Option (a) is cleaner.

### Design drift not addressed
- **Agent registry fallback is still "return XAgent()" for unknown platforms** (`services/agents/__init__.py:31`). The `Candidate.platform` schema allows `mock` and `other` — both fall back to XAgent and produce a DMCA notice pointing at `copyright@twitter.com`. For a request with `platform="telegram"` typo'd as `platfrom="telegrum"`, the system silently files a malformed notice against the wrong provider. Either raise on unknown, or add a `GenericAgent` that produces a jurisdiction-aware but provider-unbranded notice. Low priority — not triggered on the demo path.

### Dead code / minor
- **`likeness_embedding_id: str | None`** on `AthleteEnrollment` is still only ever `None` — no write path exists. Either remove the field for Phase 1, or plumb a stub-write in `/athlete/enroll` when an optional `likeness_sample` is supplied.
- **`tailwind-merge` in `frontend/package.json`** is still listed and unused. Run `npm uninstall tailwind-merge` or delete the line. Ships an unused 4KB in the bundle.
- **`file_notice` still mutates the Pydantic model in place** (takedown.py:142-150). Works in Pydantic v2 but frowned upon. Not worth fixing — low harm, would require touching all callers.
- **Brand consistency (Aegis vs Pramāṇ)** — unresolved. Still `Aegis` throughout README, i18n strings, HTML title, package.json, Python env vars. This isn't an implementer decision — it's a team/product call. Either (a) keep Aegis and drop Pramāṇ from the pitch, or (b) rename with `rg -l aegis | xargs sed` pass. Pick one before the demo. Keeping both is the worst outcome.

---

## New issues introduced in v2

Nothing net-new of significance. Two micro-observations:

- **v2 added `AEGIS_DEMO_MODE` as a runtime env flag** but it is *not* documented in the README env-var table (README still lists only the v1 vars). Add a row.
- **v2's new `/demo/status` endpoint is public and unauthenticated.** Reveals which credentials are present on the process (`gemini_live: true`, `vector_search_configured: true`). On a private demo URL this is fine. In any hardened deployment, gate it. Not a Phase-1 blocker.

---

## Verdict

v2 is a qualitatively different submission from v1.

**Ship after:**
1. Fix Candidate persistence in `/detect` — 10 minutes of work. Without this, the demo's takedown step 404s.
2. Decide Aegis-vs-Pramāṇ and align pitch + code.

Everything else on the residual list is nice-to-fix, not ship-blocking. The codebase is in better shape than typical Phase-1 hackathon submissions, the docs are honest about what was built and what wasn't, and the ethics story — especially the watermark-never-stripped commitment — reads as architecture, not ornament. Which is exactly what the "Alignment With Cause" 25% slice rewards.

**Priority order for the final hours:**

1. Candidate persistence bug (ship-blocker)
2. Brand decision
3. `likeness_embedding_id` — either write-path or remove field
4. README env-var table — add `AEGIS_DEMO_MODE`
5. Everything else — ignore until Phase 2

Stop iterating after #4. Record the demo.
