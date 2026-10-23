# Implementation tickets for specs #21–#25

The user approved publication on 2026-10-23. The ten new tickets were published as #31–#40, with exact numbered branches, parent sub-issue links, native blocking links, full contracts, and `ready-for-agent` labels. This file preserves the reviewed draft breakdown; the GitHub issue bodies are authoritative. Publication is not implementation authorization.

| Spec | Published tickets | Branch |
| --- | --- | --- |
| #22 | #31 → #32 | `31` |
| #23 | #33 → #34 → #35 | `33` |
| #24 | #36 → #37 → #38 | `36` |
| #25 | #39 → #40 | `39` |

## Existing #21 tickets

- [#26](https://github.com/sanketsingh27/bibi/issues/26): secure OpenRouter key. Implementation commit exists; browser verification and user acceptance are pending.
- [#27](https://github.com/sanketsingh27/bibi/issues/27): compatible model selection. Blocked by accepted, integrated #26.
- [#28](https://github.com/sanketsingh27/bibi/issues/28): bounded inference runtime. Blocked by #27 and live-inference prerequisites.

Do not duplicate these. Their recorded `main` base and `feature/...` branches predate the current `dev` and numbered-branch policy. Reconcile that conflict explicitly before a fresh implementation handoff; preserve #26's existing commit and branch history.

## Publication rules used for the drafts below

- Publish in dependency order after breakdown approval. Replace each draft key with its GitHub issue number and links.
- Base branch: `dev`. The first issue in each related sequence owns a branch named **only its issue number**. Record that exact number in all tickets in its sequence after issue creation, with execution order. Do not guess issue numbers in advance.
- Worktree: unassigned during planning. At implementation handoff, record either `/Users/sanketsingh/Desktop/alchemy/feature-one` or `/Users/sanketsingh/Desktop/alchemy/feature-two` after verifying it is available and assigned to that branch. The two-worktree limit applies.
- Every ticket needs explicit user approval of this breakdown before publication. Publication does not authorize implementation. Record later authorization, actual test/runtime evidence, commit, and final acceptance on the issue; do not invent them.
- Common commands: from `backend/`, `.venv/bin/python -m pytest -q` (after `uv sync --frozen` when needed); from `frontend/`, `npm run build`. For browser smoke, run `backend/.venv/bin/python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1` from `backend/` and `npm run start -- --hostname 127.0.0.1 --port 3000` from `frontend/`, then inspect `http://127.0.0.1:3000`. Use different free local ports if occupied; record them. Automated tests use real FastAPI/HTTPX routing with controlled upstream responses/time, following `backend/tests/test_search.py`. No new frontend test framework or production fixture endpoints.
- External prerequisites for affected tickets: verify applicable permission/terms for persistent public review reuse and external AI processing; use only authorized OpenRouter key/model/credits for paid smoke; perform explicit local embedding setup. Record the result as a blocker if unresolved.

## D1 — Select a listing and open its exact detail page

- **Parent spec/stories:** [#22](https://github.com/sanketsingh27/bibi/issues/22), stories 1–3, 8, 14–17, 22; consolidated [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** From either search mode, explicitly confirm a listing and open a bookmarkable page keyed by numeric Apple ID and storefront. Add exact-ID backend lookup and a minimal real identity/header view. Keep search state when returning within the same navigation session.
- **Out of scope:** Full optional metadata gallery, reviews, AI, comparison, auto-selection of ambiguous names.
- **Branch/order:** First issue on this numbered branch; D2 follows on the same branch. Base `dev`; worktree unassigned.
- **Blocked by:** None beyond existing discovery. Prerequisite: verify listing/artwork usage terms before rendering source assets.
- **Acceptance:** Exact ID/storefront lookup; invalid identity fails before Apple dispatch; wrong/missing software record is unavailable without substitution; original App Store link is safe; both modes preserve submitted results and unsubmitted draft on back; reload retains detail identity; search/catalog routes still work without AI configuration.
- **Tests:** Add `backend/tests/test_app_details.py` using real ASGI HTTP calls and controlled Apple responses for exact match, mismatch, invalid ID/country, safe URL, cache/shared request, timeout/budget, and unaffected static routes. Run that file and the common backend/frontend commands; expect all pass.
- **Runtime:** Search by keyword and app name, explicitly choose similarly named results, open each page, reload, and go back. Observe correct ID/storefront and preserved draft/results with no extra search dispatch.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## D2 — Complete the accessible app detail page

- **Parent spec/stories:** [#22](https://github.com/sanketsingh27/bibi/issues/22), stories 4–7, 9–13, 18–21; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Show available description, screenshots, category, ratings, price/version/release details and safe source attribution. Add Analysis, Reviews, Competitors tabs with honest loading/unavailable/configuration states and a saved-snapshot fallback when lookup fails. Preserve current identity against late responses.
- **Out of scope:** Fabricated analysis/review/competitor results, review fetching, paid work on tab changes.
- **Branch/order:** D1 then D2, same first-ticket numbered branch. Base `dev`; worktree inherited from D1.
- **Blocked by:** D1 verified, approved, and committed on this shared branch.
- **Acceptance:** Missing fields say unavailable; zero ratings stay zero and are labelled listing ratings; unsafe URLs and executable text do not render; failed images retain readable identity; late old-app/storefront responses cannot overwrite current view; tabs and focus work by keyboard; narrow layouts have no page overflow; saved data is marked saved when live lookup fails; tab changes send no paid request.
- **Tests:** Extend `backend/tests/test_app_details.py` for optional null/zero fields, malformed source data and unsafe URLs. Run targeted test and common full suite/build; expect pass. Browser behavior is required separately.
- **Runtime:** With a temporary controlled upstream, delay one lookup then switch app/storefront; release it and observe no overwrite. Show missing fields, failed artwork and saved fallback. Check keyboard tabs/focus and 320/768/1440-pixel widths; inspect network for no tab-triggered paid calls.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## R1 — Collect and display a bounded written-review sample

- **Parent spec/stories:** [#23](https://github.com/sanketsingh27/bibi/issues/23), stories 1–10, 15–18; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Selecting a listing starts a real, bounded mixed-star public JSON collection and displays normalized written reviews with actual count, target, page gaps, and source availability. Implement the initial review-fetch operation/poll path needed to expose real progress.
- **Out of scope:** 500 expansion, cancellation/resume, persistence, AI analysis, global review-count claims.
- **Branch/order:** First issue on this numbered branch; R2 and R3 follow sequentially. Base `dev`; worktree unassigned.
- **Blocked by:** D2 sequence accepted and merged to `dev`. Prerequisite: review-source permission/terms for persistence and later AI use resolved before affected implementation.
- **Acceptance:** Initial target 200, at most ten pages/one attempt each, sequential paced requests sharing Apple budget; empty intermediate pages do not stop later page inspection; deduplicate valid review IDs; exclude malformed records with warnings; distinguish empty feed from source failure; app/storefront never mix; no author/profile metadata retained; no collection from catalog search alone.
- **Tests:** Add `backend/tests/test_review_fetches.py` at real API seam with array/single-entry feeds, metadata entries, invalid IDs/stars/text, duplicate IDs, page 2–3 empty/page 4 populated, ten-page/200 bounds, malformed envelope, invalid scope, and dispatch-budget behavior. Run targeted file and common full suite/build; expect pass.
- **Runtime:** Select a real app, watch operation progress and actual count/target/gaps, inspect normalized records and network pages; with controlled feed, reproduce empty intermediate pages followed by a populated page.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## R2 — Expand, cancel, and resume review collection

- **Parent spec/stories:** [#23](https://github.com/sanketsingh27/bibi/issues/23), stories 3, 11–16, 32–33; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Let a researcher explicitly request target 500, cancel active collection, and resume a partial or rate-limited same-scope operation without repeating successful pages. Complete shared process-local operation lifecycle and safe poll/cancel controls.
- **Out of scope:** Automatic retry, unlimited pages, durable exactly-once claims, new review sources.
- **Branch/order:** R1 then R2, same first-ticket numbered branch; R3 follows. Base `dev`; worktree inherited.
- **Blocked by:** R1 verified, approved, and committed on the shared branch.
- **Acceptance:** 500 is an explicit target, not a guarantee; cancellation stops further dispatch and retains completed records; Retry-After pauses with a visible resume time; successful pages are reused; same requestId/payload joins, changed payload conflicts; unknown operation after restart is reported honestly; progress and terminal states match actual work; host/origin protections cover paid-capable/local operations.
- **Tests:** Extend `backend/tests/test_review_fetches.py` for 500 bound, cancellation while pacing, rate limit/Retry-After, partial results, explicit resume, replay/conflict, unknown operation, and no automatic retry. Run targeted file and common suite/build; expect pass.
- **Runtime:** Request 500, cancel between controlled pages, inspect retained count and dispatches, then resume. Simulate rate limit and restart; observe explicit recovery and no false completed state.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## R3 — Save, filter, refresh, and delete local research

- **Parent spec/stories:** [#23](https://github.com/sanketsingh27/bibi/issues/23), stories 19–31, 34; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Persist listing snapshots and versioned review samples in IndexedDB. Provide Saved research, exact local star filters, explicit refresh, and scoped deletion with derived-data invalidation hooks for later analysis/comparison.
- **Out of scope:** AI report generation, server research database, cross-device sync.
- **Branch/order:** R1 → R2 → R3 on the same first-ticket numbered branch. Base `dev`; worktree inherited.
- **Blocked by:** R2 verified, approved, and committed on the shared branch.
- **Acceptance:** Reopen saved app/storefront with no Apple/AI call; filters use stored integer stars and label sample counts; fingerprint changes on substantive content, not fetch time alone; cited historical sample versions remain available until deletion; failed/empty refresh preserves prior valid data; quota/transaction errors show not-saved state; deleting one scope removes dependent indexes/reports/comparisons but leaves other scopes and OS key; fetching more preserves old report coverage for later consumer.
- **Tests:** Extend real API tests for validation of browser-supplied sample/fingerprint/page observations, refresh replacement without count inflation, and prior snapshot preservation after failed source work. Run targeted file and common full suite/build; expect pass. Verify IndexedDB semantics in browser runtime.
- **Runtime:** Save, reload and reopen with network inspection; filter three stars and All; refresh into changed source text, then trigger storage failure and delete one scope. Observe retained old snapshot on failure, accurate storage state, and independent key/other-app data.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## A1 — Explicit local embedding setup and scoped index

- **Parent spec/stories:** [#24](https://github.com/sanketsingh27/bibi/issues/24), stories 22–29, 33; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Offer explicit first-use download/setup for the pinned local embedding model, then chunk and index saved reviews locally with source offsets and exact app/storefront/sample/model revision. Expose readiness and retrieval only for matching scope.
- **Out of scope:** Hosted embeddings, AI-generated report, silent download, quality guarantee.
- **Branch/order:** First issue on this numbered branch; A2 and A3 follow. Base `dev`; worktree unassigned.
- **Blocked by:** R3 accepted/merged into `dev`; #28 accepted/merged into `dev` before the analysis sequence. Prerequisites: explicit weight download, pinned dependency/runtime compatibility and local resource check.
- **Acceptance:** Setup requires explicit action and shows progress/error; pinned `intfloat/multilingual-e5-small` revision, CPU default, query/passage prefixes, bounded token chunks with overlap and offsets; finite normalized 384-dimensional vectors; no network embedding call after cached setup; stale/wrong-scope/revision/dimension vectors rejected; retrieval filters scope before ranking and returns at most five distinct source IDs/topic.
- **Tests:** Add `backend/tests/test_review_analysis.py` with real HTTP setup/index/retrieval boundary and deterministic vector fixtures for wrong scope/revision/non-finite vectors, duplicate chunks, offsets, and no remote embedding dispatch. Run targeted file and common suite/build; expect pass. Controlled fixtures do not prove semantic quality.
- **Runtime:** Explicitly install pinned weights, index a small battery-versus-price corpus, inspect relevant ranking and source offsets, then disable network and repeat from cache. Observe no OpenRouter embedding request.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## A2 — Analyse the complete saved review sample with valid evidence

- **Parent spec/stories:** [#24](https://github.com/sanketsingh27/bibi/issues/24), stories 1–12, 21, 30–32, 34; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** When a newly selected non-empty sample and prerequisites are ready, run bounded complete-sample analysis using the selected OpenRouter model. Show praise, complaints, requests, and opportunities with checked review quotes/IDs, provenance, and source limitations. Save the validated report.
- **Out of scope:** Top-k-only analysis, market-wide claims, filtered reports, automatic reruns after reopening.
- **Branch/order:** A1 then A2; A3 follows on same first-ticket numbered branch. Base `dev`; worktree inherited.
- **Blocked by:** A1 verified, approved, and committed on shared branch; #28 accepted and available per A1 gate. Authorized key/model/credits and permitted external review processing required for live smoke.
- **Acceptance:** Empty sample makes no provider call; long review endings survive segmentation; every selected review is processed; quote text/IDs/app/storefront/fingerprint validate before save; counts use unique supporting review IDs; small/gapped samples are labelled; captured model stays fixed through the operation; prior valid report survives cancellation, invalid provider output, or storage failure; no author/profile data in AI payload.
- **Tests:** Extend `backend/tests/test_review_analysis.py` using controlled OpenRouter responses for multi-batch complete coverage, late-text evidence, wrong/fabricated citations, empty input, count denominators, same-intent replay, model capture, failure preservation. Run targeted file and common suite/build; expect pass.
- **Runtime:** Analyse a real non-empty sample with an authorized key. Inspect all four finding types, click source evidence, verify exact review text/ID and sample count/model/time, and judge claim support. Exercise controlled bad output without replacing prior report.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## A3 — Analyse filtered reviews and update report coverage explicitly

- **Parent spec/stories:** [#24](https://github.com/sanketsingh27/bibi/issues/24), stories 13–20, 25, 33–34; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Add explicit Analyse filtered reviews and Update analysis actions. Keep separate complete/filtered reports and show analysed-versus-saved coverage, model, time, sample fingerprint, and stale-index/report state after source or model changes.
- **Out of scope:** Paid work from ordinary filter/tab/model changes, automatic replacement of old reports.
- **Branch/order:** A1 → A2 → A3 on same first-ticket numbered branch. Base `dev`; worktree inherited.
- **Blocked by:** A2 verified, approved, and committed on shared branch.
- **Acceptance:** Viewing one star sends no provider call; explicit filtered action analyses only matching saved IDs and stores separate report; no matches makes no call; fetch-more preserves prior report and labels coverage; Update analysis alone pays for expanded scope; changed sample/index/model is not relabelled current; failed update preserves prior report and evidence link to historical source version; reopening sends no paid call.
- **Tests:** Extend `backend/tests/test_review_analysis.py` for one-star scope versus complete scope, no matches, stale associations, explicit update, malformed saved index, and failed update preservation. Run targeted file and common suite/build; expect pass.
- **Runtime:** Filter to one star with network inspection, explicitly analyse it, expand sample and observe old coverage, then Update analysis. Change model/reload and verify no automatic rerun; check evidence links and keyboard/narrow layout.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## C1 — Suggest and manually select competitor candidates

- **Parent spec/stories:** [#25](https://github.com/sanketsingh27/bibi/issues/25), stories 1–13; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** On Competitors tab, generate at most five actual same-problem/category candidate suggestions with reasons; offer app-name Add app with explicit listing confirmation and select up to three candidates. None start selected.
- **Out of scope:** Automatically analysing every suggestion, verified competitor classification, side-by-side report.
- **Branch/order:** First issue on this numbered branch; C2 follows. Base `dev`; worktree unassigned.
- **Blocked by:** D2 and A3 feature sequences accepted and merged into `dev` (satisfying #25 capability dependencies). Authorized model/key/credits for real suggestions; manual addition works without them.
- **Acceptance:** At most one problem and one category Apple search per suggestion intent, at most 50 source matches each; actual returned IDs only, original/duplicates excluded; fewer than five shown honestly; reasons distinguish same-problem/category; invalid model-picked ID rejected; no automatic candidate review fetch; manual ambiguous result requires confirmation; original/duplicate/cross-storefront/fourth selection rejected before any work; keyboard and narrow-screen controls work.
- **Tests:** Add `backend/tests/test_competitors.py` with real HTTP operation and controlled Apple/OpenRouter results: fewer than five, duplicate/original, missing metadata, wrong generated IDs, search bounds, no review dispatch, and invalid selection before provider/source calls. Run targeted file and common suite/build; expect pass.
- **Runtime:** Select a real app and inspect candidate IDs/reasons/no preselection; use ambiguous Add app and confirm intended listing; attempt invalid/fourth selection while inspecting network for no bulk review work.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.

## C2 — Run and save an evidence-linked competitor comparison

- **Parent spec/stories:** [#25](https://github.com/sanketsingh27/bibi/issues/25), stories 14–33; [#20](https://github.com/sanketsingh27/bibi/issues/20).
- **What to build:** Explicit Analyse competitors runs bounded research for original plus one to three chosen apps, reuses compatible saved data, and presents a side-by-side, evidence-linked comparison. Save report/provenance locally and keep unavailable columns honest.
- **Out of scope:** Overall winner, automatic reruns, unbounded work, fabricated findings.
- **Branch/order:** C1 then C2 on same first-ticket numbered branch. Base `dev`; worktree inherited.
- **Blocked by:** C1 verified, approved, and committed on shared branch. Authorized OpenRouter credentials/credits, source permissions and local model readiness for live smoke.
- **Acceptance:** Zero/fourth/duplicate/cross-storefront inputs fail before dispatch; compare only selected scopes; reuse exact matching sample/report/index/model associations and show source age; missing data uses existing 200/500 and ten-page bounds; sequential inference captures selected model; cancel/failure preserves previous comparison; fewer than two usable scopes yields limitation, no invented comparison; per-app quotes/IDs/fingerprints validate; counts are distinct review IDs, unequal coverage is visible, no overall winner; changed source/model/selection marks old report stale; deleting source invalidates dependent evidence; reopen makes no paid call.
- **Tests:** Extend `backend/tests/test_competitors.py` with selected-scope dispatch/reuse, stale data, cancellation/partial result, insufficient evidence, cross-app citations/vector rejection, quote/count validation, model capture, replay/conflict, and prior report preservation. Run targeted file and common suite/build; expect pass.
- **Runtime:** With authorized key, compare original plus selected apps; inspect progress, sample counts/age, model, all four finding categories and clickable correct-app evidence. Simulate one unavailable app and cancellation with controlled upstream; check old report retention. Change model/selection, reopen, delete one source, and verify staleness/dependent evidence behavior on desktop and narrow screens.
- **Evidence:** Approval to publish pending; implementation authorization, verification, commit, and acceptance pending.
