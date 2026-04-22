Aegis Phase-1 Audit — Report
I reviewed the backend, agents, crawler, mock platforms, benchmark, and demo driver (roughly 60% of the codebase). Below are concrete findings grouped by severity. I didn't get through the frontend, tests, or a few smaller modules, so flag where I'm less confident.
Bugs that will fail the demo

Clip.c2pa_manifest_url is typed HttpUrl but ingest assigns file://... (ingest.py:197, schema.py:51). Pydantic will reject the file:// scheme and /ingest will 500 on every upload. Either change the schema field to str or write the manifest to a served HTTP path. Fastest fix: c2pa_manifest_url: str.
Same issue on Candidate.url and TakedownNotice.target_url. The demo seeder sends https://aegis-test-domain.example/..., which pydantic's HttpUrl validator will accept, so this one probably passes — but anything coming from the crawler with file:// prefixes (benchmark/run.py:139 sends file://benchmark/{video.name}) will fail validation before it reaches detection. Benchmark run throws on the first candidate.
stage1_retrieve re-embeds on every candidate by passing a list of frame embeddings where query_top_k expects a single query vector per call. Look at vector_index._query_local — it does q @ e.T where q is (N_frames_candidate, D) and e is (N_frames_clip, D). That works algebraically (best frame-to-frame sim), but _query_gcp loops and calls find_neighbors per frame, then dedupes per-clip. These two paths return different "cosine" semantics — LOCAL gives you best-of-cross-product, GCP gives you best-per-query-frame max-pooled. Thresholds tuned on LOCAL won't transfer.
main.py imports Candidate from backend.schema but never uses it (line 35). Minor — but it's the only unused import of several; the whole import block is sloppy enough that a ruff --fix pass should happen before submission.
Mock verdict operator-precedence bug in services/mock_platforms/app.py:69:

python   if notice.jurisdiction == "IN" and "synthetic" in notice.body.lower() or "morphed" in notice.body.lower() or "Rule 3(2)(b)" in notice.body:
Without parens, this reads as (A and B) or C or D — the 24-hour SLA fires for any notice containing "morphed" or "Rule 3(2)(b)" regardless of jurisdiction. Wrap the second clause: ... == "IN" and ("synthetic" in ... or "morphed" in ... or "Rule 3(2)(b)" in ...).
Runtime / error-handling issues

detect.py:240-241 uses callable as a type hint instead of Callable. Runs on Python 3.12+ (just a name) but will crash on older runtimes if type-checking is enabled and pylance/mypy will flag it. Replace with Callable[[str], Clip | None] and Callable[[str], Path] from typing.
_flush_pending_leaves race condition. _PENDING.append(leaf) and batch = list(_PENDING); _PENDING.clear() are not atomic under FastAPI's async workers. Under any concurrent /ingest or /detect, leaves can be lost between append and clear. Wrap in a threading.Lock (or, better, an asyncio.Lock since the handlers are async).
AegisStore.get_clip_video raises KeyError instead of returning None (storage.py:70-71). detect.py:255 does resolve_video(best.clip_id) and doesn't catch — if the clip was ingested in a prior process lifetime (Firestore mode persists, in-memory _clip_videos doesn't), detection will 500. In LOCAL mode this is fine; in GCP mode the video registry is lost on restart.
ingest.py:179 computes embeddings then discards them with _. Then main.py:108-110 re-extracts keyframes and recomputes embeddings. Wasteful but not buggy — doubles ingestion time and doubles Vertex AI cost.
Crawler honors robots.txt too aggressively. RobotsCache.allowed defaults to disallow_all_parser() on any robots.txt fetch error (line 80-82). Many hosts legitimately serve robots.txt with transient errors; a single timeout blocks the whole host for the crawler's lifetime. A 404 on robots.txt should mean "allow by default" per RFC 9309, not "deny." This will silently drop real seeds in the demo if one fetch fails.
_host_provider_of, _dmca_agent_email, _resolve_mock_endpoint in takedown.py swallow all exceptions (lines 183-203). If the agent registry has a bug, you get "[host provider unknown]" silently baked into the DMCA notice and the demo ships with a broken-looking takedown. Catch KeyError specifically; let everything else raise.

Logic errors / misalignments

Benchmark "correctness" is a no-op. _update_summary in benchmark/run.py:189-205 marks every matched variant as "correct" regardless of whether the retrieved clip_id matches the expected source clip. The comment even admits this: "we simply check that something matched." This means your reported recall is actually "match rate" — you cannot distinguish "found the right clip" from "found some clip." Fix: store a source_stem → clip_id map after _ingest_originals and compare.
_call_gemini passes raw video bytes as Part.from_data (detect.py:171). Vertex's Part.from_data accepts bytes but Gemini 2.5 Pro has video input size limits (~7 MB inline, otherwise needs a Cloud Storage URI). Any clip over ~7 MB will silently truncate or error. Switch to Part.from_uri(gs_uri, mime_type=...) for anything substantive. For Phase 1 demo clips <7 MB, you'll get lucky.
stage2_verdict sends BOTH videos to Gemini every time (line 138). That's 2× the bytes, 2× the latency, and 2× the cost per detection. For most verdicts, the candidate is what needs classification — the original is already known to be the matched source. Pass the original only when genuinely needed (deepfake, edited-highlight disambiguation) or pass keyframe stills instead of full video.
pick_jurisdiction has a dead code path. takedown.py:38-55 first asks the agent, falls back to a heuristic on candidate.host_country. But every agent subclass already implements the same heuristic (check host_country == "IN"). The fallback is unreachable in practice. Not a bug — just remove one of them.
Thresholds (PHASH_ESCALATE_DISTANCE=12, EMBEDDING_ESCALATE_COSINE=0.78) are declared "tuned on the variant set" but the benchmark doesn't produce tuning data. benchmark/run.py computes recall at the currently configured thresholds, not a sweep. You cannot actually claim "≥85% recall at ≤5% FPR" without a sweep over thresholds on a labeled set that includes true negatives. Either sweep in the benchmark runner, or remove the claim from docs/benchmarks.md.
detect.py:253 picks the best match with min(... key=lambda m: (m.phash_distance, -m.embedding_cosine)). This ranks strictly by pHash distance first — a perfect embedding match (cosine=0.99) is beaten by a slightly-better pHash (phash=5 vs phash=6) even if the latter has embedding=0.45. For transforms that defeat pHash (your whole differentiation story), this biases toward lower-quality matches. Use a combined score: -(w1 * embedding_cosine + w2 * (1 - phash_distance/64)).
"Deterministic mock embedding" is not a valid stand-in for Vertex AI embeddings in the benchmark. _mock_embedding in ingest.py:100-104 tiles a SHA-256 hash to 1408 dims. A reencode produces different bytes → totally different hash → cosine ≈ 0 between original and its own reencode. So in LOCAL mode without Vertex credentials, the entire embedding stage produces garbage and Stage 1 will never escalate on any adversarial variant — only pHash can save you. Your LOCAL benchmark numbers are meaningless. Either:

Require VERTEX_AI_PROJECT for the benchmark (documented), or
Swap the mock for a local CLIP model (clip-vit-base-patch32 via transformers, ~150 MB, runs on CPU).



Scope / coherence issues

The repo is branded "Aegis" everywhere. Your plan pivoted to "Pramāṇ." FastAPI(title="Aegis", ...), AegisStore, USER_AGENT = "AegisCrawler/0.1", aegis-local-dev-key, AEGIS_* env vars. If judges look at the repo after hearing the pitch title "Pramāṇ," there's a brand mismatch. Pick one. If keeping both: README should say "Pramāṇ (internal name Aegis)" once.
The plan's "Pillar 4: Deepfake & likeness defense" is barely present in code. The only deepfake signal is a caption keyword match in _mock_verdict ("deepfake" in caption → DEEPFAKE_MANIPULATION). No classifier, no face-matching, no even a stub head. Two options:

Be honest in the deck: "Deepfake detection is Phase-2, seeded by Gemini's multimodal classification in Phase-1."
Add a bare stub: run DFDC-pretrained model (there are public HF checkpoints) on candidate keyframes, return a score, and combine with Gemini's verdict.
Option 1 is safer given 48 hours remaining; whichever you pick, fix the mismatch between the plan's Pillar 4 and the code.


Athlete enrollment stores no likeness data. AthleteEnrollment.likeness_embedding_id is always None; /athlete/enroll never touches it. The athlete-facing view therefore can't actually filter "has my likeness been misused" — it can only filter by name string. The plan's opt-in-for-likeness-dossier story isn't wired.
Merkle receipt association is fragile. store.put_merkle_receipt(receipt, detection_ids) is passed [l.id for l in batch] in _flush_pending_leaves, but the ids in _PENDING include clip_ids (from ingest) and notice_ids (from takedown), not only detection_ids. So /verify/{detection_id} can only return a receipt if the detection's verdict was the leaf id — which build_leaf_for_verdict(verdict.detection_id, ...) does guarantee, so this works — but the sibling leaves for clips and notices get keyed under ids that /verify/{detection_id} will never look up. Dead storage. Fix: key receipts by all leaf ids (which the function already does, good) but understand that /verify/{clip_id} and /verify/{notice_id} aren't exposed. Either add those routes or narrow the storage to detection_ids only.
file_notice assigns to notice.filed_at, notice.status, etc., mutating a Pydantic model in place (takedown.py:156-164). Works in Pydantic v2 by default but is frowned upon — use notice.model_copy(update={...}) or make TakedownNotice frozen. Minor.

Improvements without overengineering

Add one pre-commit check that runs ruff check backend services benchmark demo and mypy backend. The unused imports, the callable-instead-of-Callable, and several type drift issues would all be caught. Two-line .pre-commit-config.yaml, one-time cost, pays back immediately.
Idempotency on /ingest. A retried POST currently creates a duplicate Clip with a new UUID. One line: hash the video bytes and key on that — if it exists, return the existing clip_id.
Remove the "deepfake or fake in caption" rule from _mock_verdict (line 200). It leaks into demo fallback and encourages judges to think caption-matching is your deepfake detector. Either remove, or gate behind a AEGIS_DEMO_MODE=true env var and document it.
Add /demo/status endpoint that returns {index_mode, storage_mode, kms_mode, anchor_mode, gemini_live}. The demo operator currently has no way to confirm they're running in GCP vs LOCAL mode without grep-ing env vars. Two minutes to add, saves 20 minutes of demo-day confusion.
Consolidate _call_gemini in detect.py and _call_gemini_for_draft in takedown.py into a shared backend/gemini.py with one call(...) function. Two almost-identical fallback branches is fragile; the mock paths diverge over time and the real paths will drift.
Record the actual threshold sweep in benchmark/run.py as an optional --sweep flag. Emit a thresholds.json with recall/FPR curves. This is the single artifact that converts "we have benchmarks" (caps at ~28/40 on technical merit, per your own plan) into "we have tuned benchmarks" (supports the 32+ claim).
frontend/ (not reviewed here): based on the file tree, I see VerifyPage.tsx, AthleteView.tsx, RightsHolderDashboard.tsx, a BilingualAlert component and i18n.ts. Confirm the athlete view is the default landing route (your plan commits to this for the DRM-preempt story). If main.tsx routes / to the rights-holder dashboard, fix it.


Priority fix list (ranked by risk × effort)
Fix before demo record (highest leverage):

HttpUrl → str on c2pa_manifest_url and anywhere else file:// appears (#1, #2).
Async lock on _PENDING batch flush (#7).
Operator-precedence fix in mock platform SLA logic (#5).
Benchmark correctness — map sources to clip_ids and actually check (#12).
Remove double-embedding in /ingest (#9).
Fix the "best match" ranker to use combined score (#17).
Swap _mock_embedding for a real CPU CLIP model OR document that benchmarks require VERTEX_AI_PROJECT (#18).
Brand consistency: Aegis vs Pramāṇ (#19).

Fix before Phase-2 refinement:
9. Threshold sweep in benchmark runner (#29).
10. Deepfake pillar either stubbed or honestly downgraded in docs (#20).
11. Athlete likeness embedding wired end-to-end or removed from the schema (#21).
12. Video-size handling for Gemini Part uploads (#13).
Skip for now (overengineering): don't rewrite the agent interface, don't add ADK, don't split Gemini calls. Those are Phase-2 risks, not Phase-1 bugs.
The codebase is in better shape than I expected — the architecture is coherent, the LOCAL/GCP split is clean, the fallback story is honest. The bugs above are real but tractable in a few hours of focused work. The single highest-leverage fix is #18 (embedding mock is broken); without it, your LOCAL benchmark numbers are fictional and the demo only works because pHash carries it.
Want me to dig into the frontend and tests next, or focus on one of the priority fixes?You said: ContinueContinue20:09Claude responded: Aegis Audit — Part 2: Frontend, Tests, Infra, DocsViewed 11 files, ran 9 commandsViewed 11 files, ran 9 commandsAegis Audit — Part 2: Frontend, Tests, Infra, Docs
Additional bugs
31. Footer links point to /docs/*.md (App.tsx:49-51). Raw markdown files aren't routes — they'll 404 on Firebase Hosting. Either (a) put the docs in frontend/public/ as .md files and serve them static, (b) render them in-app via a MarkdownViewer, or (c) link to GitHub instead. Currently those links are broken. Judges will click them.
32. Frontend brand is "Aegis" throughout (i18n.ts:8, index.html:10, package.json:2). Same mismatch-with-plan issue — if the pitch says Pramāṇ, every frontend surface contradicts it.
33. RightsHolderDashboard renders hardcoded demo data. No API fetch, no loading state, no error state. The table is a screenshot with a slight animation. For Phase 1 this is fine, but the README claims "real-time listener" in spirit; deck should not overclaim.
34. Missing clsx declaration. App.tsx, LanguageToggle.tsx, BilingualAlert.tsx import clsx, but package.json only declares clsx@^2.1.1 — good. However tailwind-merge is declared and never used. Minor — dead dep.
35. TS noUnusedParameters will break the build. RightsHolderDashboard imports useTranslation and declares const { t } = useTranslation(); then only uses t in two places. Safe. But VerifyPage.tsx imports useParams and uses it — check passes. Run npm run build before submission; tsconfig is strict.
36. AthleteView "See drafted takedowns" button has no onClick. Clicking does nothing. Either wire it to /rights-holder or remove it for Phase 1. A dead button during the demo is worse than no button.
37. VerifyPage calls verifyReceipt on form submit but has no way to find a detection_id from the athlete view. The UX flow is broken: athlete sees an alert → has no clickable path to verify. Add "Verify this detection →" link on each BilingualAlert, or accept that the verify page is a developer-testing tool and drop it from the demo flow.
Test issues
38. test_below_threshold_does_not_file is an explicitly admitted no-op. The comment says "keeping as a TODO." If the deck is going to claim "takedown restraint" as an ethics guardrail, this test should actually exercise the below-threshold path. Generate a second unrelated clip with ffmpeg in the fixture.
39. Test leaks environment variables. tests/test_agents.py::test_agent_submit_endpoint_resolves_from_env sets MOCK_X_ENDPOINT and only pops it on success. If the assertion fires before the pop, subsequent tests see the variable. Use monkeypatch.setenv() instead of raw os.environ.
40. conftest.py uses setdefault on env vars, which means a test running in a CI where AEGIS_INDEX_MODE=GCP is set accidentally will happily try to hit real Vertex. Use monkeypatch.setenv in a session-scoped autouse fixture that overrides, not defaults.
41. test_full_pipeline asserts verdict in ("EXACT_PIRACY", "DEEPFAKE_MANIPULATION"). The caption "leaked clip" contains no deepfake keyword, so mock returns EXACT_PIRACY deterministically. The tuple assertion is loose for no reason — makes the test less useful as a regression check. Tighten to == "EXACT_PIRACY" and add a separate deepfake test.
Infra issues
42. infra/deploy.sh builds crawler with gcloud run jobs deploy --image gcr.io/...:latest without ever running gcloud builds submit to push that image. The job will fail with "image not found" on first run. Either prepend a gcloud builds submit --tag gcr.io/... step, or switch to --source ./services/crawler.
43. deploy.sh doesn't enable Vertex AI Vector Search index deployment — it warns the operator to do it manually in the console. In a 48-hour sprint this is pragmatic, but it means deploy.sh is not actually "one-shot." Rename to deploy-partial.sh or add a clear top-of-file warning about the manual step.
44. ENV_VARS array splatted with --set-env-vars "$(IFS=,; echo "${ENV_VARS[*]}")" (line 170 of deploy.sh). If any env var value contains a literal , (e.g., a URL with query params), this breaks. Use --set-env-vars "^|^${ENV_VARS[*]}" with a custom delimiter or --env-vars-file.
45. aegis-api Cloud Run deployed with --allow-unauthenticated. For a hackathon, fine. For the claim of a "trust layer," it's contradictory — any drive-by can POST /ingest and register a "signed clip." Add a README note: "Phase 1 is open; Phase 2 moves /ingest and /takedown behind Firebase Auth with a rights-holder role claim." And if possible put a toy API key check on /ingest, /takedown for Phase 1 so judges can't accidentally abuse the live URL.
Docs issues
46. docs/case-study.md says Aegis "strips" the visible watermark from the demo clip (line 32): "Aegis's pipeline is configured to recognize and strip only for the purposes of the demo." This is a bad look for an ethics-forward product — even as a demo convenience, "we strip our own safety watermark in the dashboard" will be read by a skeptical judge as "the ethics are performative." Either (a) leave the watermark visible in the dashboard too (best — it reinforces the constructed-scenario framing), or (b) don't document this in the ethics-adjacent doc.
47. docs/case-study.md says dataset cards are "Phase 2 — sources cited inline for Phase 1", but docs/dataset-cards/dfdc.md and docs/dataset-cards/celeb-df.md already exist. Delete the "Phase 2" disclaimer — you shipped them.
48. README's "repository map" lists benchmark/generate_variants.py but not benchmark/run.py even though the latter is the benchmark runner. Incomplete.
49. README claims "Gemini 2.5 Pro semantic verdict" and "deepfake / likeness-abuse verdict triggers a bilingual alert." The first is accurate. The second is misleading — there is no deepfake classifier; verdicts only become DEEPFAKE_MANIPULATION when (a) the _mock_verdict sees "deepfake" in the caption, or (b) Gemini decides so in the verdict prompt. You don't have a likeness classifier. The README overclaims a pillar. Either add Gemini-based zero-shot reasoning as the "classifier" (which you already have, just own it honestly in the README) or downgrade the language.
50. docs/architecture.md references "Google ADK" but the code uses a single-process agent registry. You already have the fallback documented in the plan ("single Gemini orchestrator with platform adapters"), but the architecture doc doesn't reflect that choice. Either note the fallback explicitly in architecture.md, or add a Phase-2 section "ADK migration path."

Updated priority list
The first audit flagged 30 issues. Second pass added 20 more. Cutting to what matters for Phase 1 submission:
Must-fix before recording the demo (breaks the actual user-visible flow):

#1, #2: HttpUrl → str on c2pa_manifest_url (API will 500)
#31: Footer doc links 404 (judges will click)
#36: Dead "See takedowns" button
#18: Mock embeddings are broken — either use CPU CLIP or require Vertex for benchmarks
#19 + #32: Brand consistency (Aegis vs Pramāṇ — decide)
#46: Watermark-stripping claim in ethics doc

Must-fix before pitch (breaks the story):

#12: Benchmark doesn't actually measure correctness — numbers in deck will be wrong
#20 + #49: Deepfake pillar misalignment — either add a real signal or honestly downgrade
#42: Crawler image never built — deploy.sh fails

Nice-to-fix if time (hardens the codebase):

#5, #7, #8, #10, #11, #39, #40 — small correctness + test hygiene
#33: Rights-holder dashboard hardcoded (acceptable for Phase 1; note in README)
#44, #45: Deploy script robustness

Skip (premature, overengineering for Phase 1):

ADK migration
Real platform submission
Propagation graph (already stubbed honestly)
Federated learning, SportSig-Bench at scale

Bottom line
The codebase is consistent with a serious 48-hour sprint. The strategic framing (DRM-preempt, ConstructedBanner, ethics doc, SDG reframe) is shipped, not sprinkled — that's rare for hackathon code and it's the single biggest asset you have. Architecture choices (LOCAL/GCP split, fallback-mode discipline, deterministic mocks) are mature.
The three deepest concerns:

The benchmark doesn't measure what it claims to measure. Recall == match rate. This undermines your 40% technical merit slice harder than any other bug. Fix #12 first.
The "deepfake pillar" is thinner than the docs imply. Gemini zero-shot is a legitimate Phase-1 approach — own it explicitly. Don't let judges discover the gap; name it first.
Frontend and backend disagree about whose authenticity is being attested. AegisStore vs "Pramāṇ" pitch, and documented-watermark-stripping vs ethics-forward framing — small things, but they compound.