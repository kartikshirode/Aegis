# Aegis Audit — v3

Diff v2 → v3 and fresh scan of the codebase.

---

## Summary

v3 is a small, targeted change set — 9 files modified, 1 file added. Every change cleanly addresses a v2 residual. No regressions introduced by the changes.

The v2 ship-blocker (unpersisted Candidate breaking `/takedown`) is **fixed** with good discipline: fix the bug + add a regression test. The GenericAgent addition solves the "typo files DMCA at copyright@twitter.com" silent-failure path. Dead code (`likeness_embedding_id`, `tailwind-merge`) removed. README env-var table rebuilt.

The residual issues in v3 are a **smaller set than v2's residuals** and are all minor: dead code, doc drift, one narrow docstring that describes a Phase-2 feature as if it's wired in.

**Verdict: Ship-ready. Nothing on this list blocks the demo. The remaining items are polish and Phase-2 prep.**

---

## v2 residuals now fixed

| Issue | Status | How |
|---|---|---|
| **Candidate never persisted → /takedown 404s (ship-blocker)** | **FIXED** | `detect.detect()` now returns `tuple[VerdictRecord, Candidate] \| None`; `main.detect_route` unpacks and calls `store.put_candidate(candidate)` before `put_verdict`. Order is correct (candidate before verdict). |
| **Regression guard for the ship-blocker** | **ADDED** | `tests/test_end_to_end.py:129` now asserts `r.status_code != 404` with a "Candidate not persisted (regression)" message. |
| **Unknown-platform agent fallback silently posts to X/Twitter endpoint** | **FIXED** | New `GenericAgent` with placeholder provider/email. A typo like `platform="telegrum"` now produces a notice with clearly-marked `[host provider — platform not recognised]` — visibly wrong rather than silently wrong. Tests enforce this. |
| **`likeness_embedding_id: str \| None` is dead** | **FIXED** | Field removed. AthleteEnrollment docstring now explains why Phase-1 deliberately stores name+language only. Ethics doc updated in lockstep. |
| **`tailwind-merge` listed and unused** | **FIXED** | Removed from `package.json`. |
| **README env-var table missing `AEGIS_DEMO_MODE`** | **FIXED** | Table rebuilt: all 14 env vars including `AEGIS_DEMO_MODE`, `AEGIS_KMS_KEY`, `AEGIS_ANCHOR_MODE`, `ALLOWED_ORIGINS`. |
| **Tests accepted loose jurisdiction fallback** | **FIXED** | Generic-agent test explicitly asserts `OTHER` (not "OTHER or US"); second test asserts the designated-agent email does not contain "twitter". |

Fix quality is strong. Each change is minimal, explanatory comments are added where judgement was exercised, and the test suite was updated in the same commit.

---

## v3 residual issues

### Low-risk bugs

**1. `_mock_embedding` effective dimensionality is 128, not 1408.** The function advertises `dim=1408` and tiles a 128-bit hash 11× to fill it. Mathematically the cosine similarity between two tiled vectors equals the cosine between the underlying 128-bit vectors — tiling is a no-op for similarity computation. This is fine for LOCAL mode (cosine tracks Hamming distance honestly), but the doc claim "1408-dim embedding" is cosmetic. Two options: (a) add a one-line comment noting the effective dimensionality, or (b) change the tiling to a learned projection. Option (a) is sufficient; docs/benchmarks.md already says LOCAL numbers are not substitutes for Vertex.

**2. `file_notice` does not catch `ValueError` from `resp.json()`.** If a platform endpoint returns a 200 with non-JSON body (e.g., Cloudflare HTML), the `except httpx.HTTPError` clause doesn't trigger and the exception propagates, leaving the notice in limbo. Mock endpoints return JSON so Phase 1 is unaffected. Two-line fix: `except (httpx.HTTPError, ValueError)`.

**3. `/athlete/enroll` wraps a 500 around a validation failure.** `EnrollRequest.preferred_language: str = "en-hi"` (accepts any string via FastAPI) but `AthleteEnrollment.preferred_language: Literal["en", "hi", "en-hi"]` (strict) — a POST with `"fr"` gets past the request validator and crashes inside the handler with an unhandled Pydantic error, producing 500 instead of 422. Fix: `preferred_language: Literal["en", "hi", "en-hi"] = "en-hi"` on `EnrollRequest`.

**4. Module-level `store = AegisStore()` leaks state between tests.** `backend.main.store` is a module-level singleton; tests share it across functions in the same session. `test_full_pipeline` ingests data that persists into `test_below_threshold_does_not_file`. The tests still pass (the unrelated clip is genuinely unrelated), but they are coupled fragilely. Right fix is a `_reset_for_tests()` method on `AegisStore` called from a function-scoped fixture. Low-priority for Phase 1; real for Phase 2.

### Documentation drift

**5. `backend/prompts/deepfake_verdict.txt` exists but is never loaded.** README, docs/architecture.md, docs/solution_brief.md, docs/dataset-cards/dfdc.md, and `backend/detect.py`'s module docstring (line 11) all reference this prompt as if it is in the Phase-1 code path. In reality no Python code reads the file — `backend/detect.py` only loads `verdict.txt`. The docs overclaim. Two fixes: (a) change docs to say "prepared for Phase 2, classifier wiring lives on the roadmap," or (b) actually wire the escalation path — if the Stage-2 verdict returns `DEEPFAKE_MANIPULATION` with borderline confidence, call Gemini again with the deepfake prompt. Option (a) is the 10-minute fix; option (b) is the honest-wiring fix. Either is acceptable.

**6. `DEEPFAKE_ESCALATION_CONFIDENCE = 0.60` constant is declared and unused.** Same root cause as #5 — dead infrastructure for a Phase-2 feature. Remove the constant or wire the escalation.

**7. `AEGIS_LOCAL_HMAC_KEY` env var undocumented.** Used in `backend/provenance/merkle.py:140` for local-mode signature verification. Not listed in README env-var table. If an operator sets it during sign but not during verify (or vice versa), signatures fail silently. One row in the README table.

**8. `/demo/status` endpoint undocumented.** Introduced in v2 to confirm real-GCP mode before recording. Not mentioned in README endpoints list, not referenced in `submission-checklist.md`, not called out in `docs/demo-cold-open.md` as a pre-flight check. The operator has to already know the URL exists. Add a step to the demo checklist: "curl $API_URL/demo/status — verify `gemini_live: true` and `vector_search_configured: true` before recording."

### Brand consistency

**9. One "Pramāṇ" leak in code.** `services/agents/__init__.py:6` docstring reads "preserves the 'agent per platform' framing from the Pramāṇ plan." Every other surface is Aegis. Change to "from the original design plan." A judge reading this `__init__.py` will see a mystery word with no referent.

### Dead code / polish

**10. `backend/main.py` has three unused imports.** `asyncio` (line 19, only mentioned in a comment), `Clip` and `VerdictRecord` (line 36-43, type-imported but unreferenced). One `ruff --fix` pass cleans these.

**11. `services/agents/__init__.py` has four unused imports.** `Candidate, Clip, Jurisdiction, VerdictRecord` on line 13 — none are referenced in the module body. Same ruff fix.

**12. `numpy` imported lazily inside `_mock_embedding`** (`backend/ingest.py:120`) while being imported at module level in `backend/vector_index.py`. Inconsistent. Move to module-level import in ingest.py too.

### Submission hygiene

**13. `Audit v1.md` and `Audit v2.md` sit at repo root.** Submission-checklist calls for a public GitHub repo. The `.gitignore` does not exclude them, so `git add .` commits them. Judges clicking through the repo will see internal bug-hunt notes. Two options: (a) add `/Audit*.md` to `.gitignore` and `git rm --cached`, or (b) move to a `/.internal/` directory that's gitignored. Do this before `git push`.

### Comment accuracy

**14. Comment at `backend/main.py:266-268` oversimplifies the concurrency model.** Says "_PENDING appends+drains can race under FastAPI's thread-pool for sync handlers." In reality both `async def ingest_route` (event loop) and `def takedown_route` (threadpool) call `_anchor_leaf` — the threading.Lock handles both correctly but the comment implies only the sync path matters. Not a bug. Correct to: "Both async handlers (on the event loop) and sync handlers (on the threadpool) call `_anchor_leaf`. threading.Lock handles both safely."

---

## Nothing of significance introduced by v3

I checked the three changed areas (tuple return from detect, GenericAgent, schema field removal) for new bugs:

- **Tuple unpack in main.py** — correct, and `if result is None` is checked before unpacking. No crash path.
- **GenericAgent** — inherits PlatformAgent, implements all four required methods, correctly defaults to `OTHER` jurisdiction, placeholder strings are clearly marked. Test coverage added.
- **`likeness_embedding_id` removal** — no code still references the field (verified with grep). Schema migration is clean because Firestore is permissive about missing fields.
- **README env-var table** — accurate against the code (spot-checked `AEGIS_ANCHOR_MODE`, `AEGIS_KMS_KEY`, `AEGIS_DEMO_MODE`).

---

## Priority order

**Before demo record** (15 minutes total):
1. Delete `Audit v1.md` and `Audit v2.md` from the repo root (#13).
2. Fix the Pramāṇ leak in `services/agents/__init__.py:6` (#9).
3. Add one line to `docs/demo-cold-open.md`: "curl API_URL/demo/status — confirm gemini_live + vector_search_configured before recording" (#8).

**Nice-to-fix before submission** (30 minutes):
4. Either wire `prompts/deepfake_verdict.txt` or downgrade docs to "Phase 2" (#5).
5. `file_notice` ValueError catch (#2).
6. `/athlete/enroll` preferred_language type tightening (#3).
7. `ruff check --fix` pass on backend + services (#10, #11, #12).

**Phase 2**:
- Module-level store → injectable (#4).
- Real deepfake escalation path (#5 option b, #6).
- Phase-2 env-var docs: `AEGIS_LOCAL_HMAC_KEY` (#7).

Items 1-3 take 15 minutes and close the only submission-visible issues. Everything else is developer polish that judges will not see.

---

## Overall assessment

v3 is a clean, focused iteration. Every v2 priority-0 and priority-1 item is addressed; the new GenericAgent is a better solution than the minimum patch would have been; the regression test for the Candidate bug shows good engineering discipline rather than just bug-patching.

The codebase is in materially better shape than typical Phase-1 hackathon submissions. Ship this.
