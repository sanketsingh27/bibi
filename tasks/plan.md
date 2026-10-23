# App Store discovery — published implementation plan

## Approval and current state

- Parent: [#14 — Local App Store discovery with Next.js and FastAPI](https://github.com/sanketsingh27/bibi/issues/14).
- In the planning conversation, the user approved the spec and ticket publication, then explicitly authorized implementation and testing of all five tickets, each in a different fresh session. This does not waive dependency integration, final acceptance, or separate commit/merge/close gates.
- All five tickets (#15–#19) are implemented, verified, explicitly accepted, committed, integrated into local `main`, and closed. All five original feature implementations used distinct fresh default-model sessions and dedicated exact-branch worktrees. No push was authorized or performed.
- Final local `main`: `3df94acaef8d54a6b259b231b1db420acb1c9aff` (`feat: switch storefronts without submitting unfinished drafts (#18)`). It contains accepted #15, scoped #16/#17/#19 plus their verified combined integration, and accepted #18. Parent spec #14 remains open and unchanged.
- Parent #14 and historical issues #1–#13 were not modified or closed.

## Separate implementation sessions

- #15: `/Users/sanketsingh/Desktop/alchemy/bibi-15-keyword-discovery`, `feature/15-keyword-discovery`, original fresh session `01a15ffd-916d-756a-9a82-233fe9e063fa`, terminal `term_3899bac6-27d0-4ba8-ba79-011b28298c9a`; [historical handoff](handoff-15.md).
- #16: `/Users/sanketsingh/Desktop/alchemy/bibi-16-listing-metadata`, `feature/16-listing-metadata`, dispatch `ctx_36887f6d9740`, fresh terminal `term_6799c638-6b06-465a-9675-bbb2660caca7`.
- #17: `/Users/sanketsingh/Desktop/alchemy/bibi-17-app-name-confirmation`, `feature/17-app-name-confirmation`, dispatch `ctx_93ce8786eddb`, fresh terminal `term_42cf7cbc-6c07-4846-832c-d0c7f7d439a2`.
- #19: `/Users/sanketsingh/Desktop/alchemy/bibi-19-search-freshness`, `feature/19-search-freshness`, dispatch `ctx_64b591d0e143`, fresh terminal `term_c4b9c193-9194-4f34-876a-bcbacf931cc9`.
- #18: `/Users/sanketsingh/Desktop/alchemy/bibi-18-storefront-switching`, `feature/18-storefront-switching`, dispatch `ctx_5d04d2da46af`, fresh terminal `term_c8ea0552-e6cc-4bde-a785-5a8b9515d0b9`; exclusive runtime lease granted.

Launch provenance confirmed different newly created agent terminals without model overrides; fresh/default-session ownership was checked before editing. Offline work ran independently where dependencies allowed, and the coordinator serialized browser/runtime verification with exclusive port-3000/8000 leases. All implementation workers settled and were released/accounted for. Separate final-main production services now run persistently on loopback: frontend http://127.0.0.1:3000, API http://127.0.0.1:8000.

The independent wave settled successfully with full [#16](https://github.com/sanketsingh27/bibi/issues/16#issuecomment-6325749839), [#17](https://github.com/sanketsingh27/bibi/issues/17#issuecomment-6325676623), and [#19](https://github.com/sanketsingh27/bibi/issues/19#issuecomment-6325807747) evidence. The user then selected “Accept and integrate all three,” explicitly authorizing scoped commits, local integration/conflict resolution with verification, and closure. Scoped commits are #16 `3ef43bd`, #17 `747afb1`, #19 `98f95bf`. One exclusive integration owner combined them on #16's branch, resolved README/page/CSS conflicts with a minimal canonical ListingRow action slot, and verified 78 API tests, production build and live/controlled combined browser behavior. [Combined evidence](https://github.com/sanketsingh27/bibi/issues/16#issuecomment-6326164258) records all original commit ancestries and integration HEAD `a015944`. Local `main` was fast-forwarded to that HEAD and the three issues closed. Workers/runtime leases were released; no push occurred.

Final [#18 evidence](https://github.com/sanketsingh27/bibi/issues/18#issuecomment-6326401549) records its 78 passing API cases, production build, live US/India/cache/metadata/copy/confirmation smoke and controlled keyboard/country/query/failure/invalid/empty/race scenarios. Actual keyboard testing caught draft submission when the picker was inside the form; moving it outside fixed the reproduced regression without key suppression. The user then selected “Accept and integrate #18”; its three scoped files were committed and fast-forwarded into local main at `3df94ac`, and #18 was closed. From that actual main checkout, the coordinator independently ran `uv sync --frozen && .venv/bin/python -m pytest` (78 passed in 2.30s), `npm ci --ignore-scripts` and the production build (passed), live API curl (HTTP 200), and a separate production-browser smoke: no search while typing; 45 keyword matches; cached repeat with unchanged fetch time; 40 explicit US Tiimo candidates; confirmed listing metadata; real clipboard ID 1480220328; India reran only Tiimo, retained draft and cleared confirmation (47 candidates); country-specific metrics; local return without a request; US/blank/Keyword/zero-row reload; empty runtime errors. Screenshot inspected, managed tab closed. Counts/metrics are observations, not fixed catalog expectations. A non-blocking Next.js warning about the ignored home-directory package-lock and first-build cache notice were recorded, not suppressed. Final test/runtime evidence is on #18; no engineering or approval blocker remains.

## Architecture and slicing decisions

Use the approved boundaries: Next.js screen → FastAPI HTTP boundary → search service → Apple HTTP adapter, plus a shared static storefront catalog. The search service owns normalization, cache, pending requests, and the upstream request budget; these are not separate deployed services. The diagram's illustrative internal symbol names do not impose a class hierarchy.

The current checkout contains only the informational landing page, not the search application or backend. Preserve that landing page unchanged. No prefactoring ticket or dependency on the historical research workspace is needed.

The approved ticket conventions establish `frontend/` for Next.js and `backend/` for FastAPI, with backend entry point `bibi.main:app`. These applications and commands do not exist yet; they are implementation deliverables, not verified runtime behavior.

The first usable search includes safe normalization, the request budget, deadline, and explicit errors. It supplies the complete API result contract; listing-metadata presentation follows as its own visible slice. Before the cache slice, `cached=false` is truthful, not a placeholder cache. Later slices reuse already functioning API layers instead of creating unnecessary endpoint changes.

## Published ticket index

| Ticket | Exact assigned branch | Base | Blocked by |
| --- | --- | --- | --- |
| [#15 — Search App Store keywords locally](https://github.com/sanketsingh27/bibi/issues/15) | `feature/15-keyword-discovery` | `main` | None |
| [#16 — Inspect listing metadata and copy app IDs](https://github.com/sanketsingh27/bibi/issues/16) | `feature/16-listing-metadata` | `main` | #15 |
| [#17 — Confirm an intended app by name](https://github.com/sanketsingh27/bibi/issues/17) | `feature/17-app-name-confirmation` | `main` | #15 |
| [#18 — Switch storefront without mixing search state](https://github.com/sanketsingh27/bibi/issues/18) | `feature/18-storefront-switching` | `main` | #17 |
| [#19 — Reuse fresh results across repeated and concurrent searches](https://github.com/sanketsingh27/bibi/issues/19) | `feature/19-search-freshness` | `main` | #15 |

Initial dependency frontier: **#15 only**. After #15 is accepted and integrated into `main`, #16, #17, and #19 may proceed independently in separate authorized sessions/worktrees. #18 requires #17's confirmation behavior to implement and prove storefront-change resets. All five must be accepted and integrated for parent-scope completion.

An issue being closed alone does not satisfy a dependency: accepted changes must be integrated into `main` and available in the implementing worktree. Independent tickets may touch the same screen/service; keep edits scoped and resolve integration conflicts without changing accepted behavior.

## Planned verification commands

Each published ticket contains its own acceptance criteria, API scenarios, exact command working directories, runtime scenario, boundaries, and approval/completion evidence.

| Purpose | Working directory | Command |
| --- | --- | --- |
| API behavioral suite | `backend/` | `python -m pytest` |
| Frontend build | `frontend/` | `npm run build` |
| Single-worker loopback backend | `backend/` | `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1` |
| Loopback frontend | `frontend/` | `npm run dev -- --hostname 127.0.0.1 --port 3000` |
| Live API smoke | Repository root | `curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/search?q=adhd%20planner&country=us&limit=50'` |

Use the approved real FastAPI pytest/HTTPX boundary with controlled Apple transport and time, plus browser runtime verification of the real application path. No separate helper/UI unit suites, production fake-data endpoints, automatic retries, or live-service exhaustion. Tests/build must pass, and each ticket's browser scenario must be observed; live failure/empty output does not prove populated behavior. Dependency setup, runtime versions, and verification documentation ship with each slice.

## Observed planning/publication verification

- The five drafts each contained all 12 required contract sections, collectively assigned all 50 parent user stories, and declared an acyclic dependency graph.
- After publication, fetched all five issue bodies and verified exact agreement with the final contracts, open state, exact branch assignments, and absence of branch placeholders.
- Created and fetched native GitHub blocking relationships: #16 → #15, #17 → #15, #18 → #17, #19 → #15; #15 has none.
- Applied `ready-for-agent` only after contract/dependency verification and fetched every ticket's labels to verify it.
- The #15 implementation session reported 64 passing real FastAPI API tests, a successful production Next.js build, zero frontend audit vulnerabilities, and live/controlled browser scenarios. Its full [verification evidence](https://github.com/sanketsingh27/bibi/issues/15#issuecomment-6325313837) includes exact commands and criterion-specific outcomes. The user subsequently accepted it and explicitly authorized its scoped commit, local merge, and closure. The scoped 19-file commit `a905e363dfaa28c329cbb279a5fea1a532fb82f7` was fast-forwarded into local `main`; #15 was closed with integration evidence. No push occurred.
- The coordinator independently exercised the actual production browser: typing caused zero search requests; Search returned 45 live `adhd planner` matches with HTTP 200/no-store, Enter returned 40 live `Tiimo` matches, runtime errors were empty, and reload cleared input/results. The screenshot was inspected and the managed tab closed; [independent evidence](https://github.com/sanketsingh27/bibi/issues/15#issuecomment-6325348342) is recorded on #15. Live counts are observations, not fixed acceptance counts.
- Supervision run `run_4ec5114ab916` adopted the original #15 session after its initial busy-readiness attempt timed out. The replacement dispatch and all later implementation/integration dispatches settled successfully; all delivered completion messages were processed/acknowledged and no reclaimable worker cleanup remained. Subsequent explicit user acceptances and local integrations completed every required gate.

## Authorization and completion

The user explicitly accepted and authorized scoped commits, local integration and closure for #15, then #16/#17/#19 (including conflict resolution and combined verification), then #18 after its final evidence. All five issues are confirmed CLOSED and all accepted source is in local main. No push/public deployment occurred. Required runtime evidence and commands are recorded per issue and in README; the final loopback production application is left running for use.

The #15 worktree ownership and fresh/default session were verified, its implementation/verification and authorized commit dispatches both settled successfully, and release operations retained its pre-existing terminal without process action. The [handoff](handoff-15.md) remains historical; this plan records current progress. #16/#17/#19 use new terminals rather than reusing the #15 session. Coordinator run `run_4ec5114ab916` owns completion reports and GitHub evidence writes; workers follow the injected prohibition on GitHub posts.

During implementation, record actual commands, working directories, results, and unmet criteria on the ticket. Request user acceptance before closing; committing, merging, and closing require the appropriate explicit authorization.
