# Fresh-session implementation handoff — issue #15

## Ownership and authorization

- Ticket: https://github.com/sanketsingh27/bibi/issues/15
- Parent spec: https://github.com/sanketsingh27/bibi/issues/14
- Exact branch: `feature/15-keyword-discovery`
- Base: `main`, baseline `99c893be4e63752464ac62eb7a433d25707403ad`
- Dedicated registered worktree: `/Users/sanketsingh/Desktop/alchemy/bibi-15-keyword-discovery`
- Orca workspace: `50f7dc22-a989-4591-9ddd-c1a7ca189740::/Users/sanketsingh/Desktop/alchemy/bibi-15-keyword-discovery`
- Receiving agent handle: `term_3899bac6-27d0-4ba8-ba79-011b28298c9a`
- Ticket #15 has no blockers. Its exact branch, worktree registration, and initially unassigned state were verified; it has now been assigned to the authenticated GitHub user and its body records this worktree.
- The user authorized all five tickets: “implement all the tickets , test it and let me know use diffrent session for each sesssion”. That authorization is recorded in comments on #15–#19. Implement **only #15** in this session.
- Other tickets remain gated by accepted changes integrated into `main`: #16/#17/#19 depend on #15, and #18 depends on #17. Do not bypass these blockers or implement another ticket here.
- The user has not supplied advance final acceptance or separate commit/merge/close authorization. After observed verification, request acceptance and required integration authorization; keep the issue open meanwhile.

## Fresh/default session requirement

This is a new OMP process launched in a unique, previously unused session directory, without model/provider/thinking/config overrides and without resume/continue flags. Launch command:

```text
'/Users/sanketsingh/Library/Application Support/Tern/omp/bin/omp' --session-dir /Users/sanketsingh/.omp/agent/sessions/bibi-issue-15-bf1a22da83fd4e8f9eaaa41be73f08d0
```

Verify use of the client's configured default from exposed session metadata/settings. Do not inherit or hard-code the planning model. If the default cannot be established from exposed information, request the user's confirmation before implementation, as required by AGENTS.md. Any correction is manual; do not change model defaults.

## Required first actions

1. Read the worktree's `AGENTS.md`, ticket #15 and all comments, and parent #14 and all comments. Follow applicable skills, including interface design, incremental implementation, behavioral testing, frontend engineering, security, and browser verification.
2. Run `git rev-parse --show-toplevel`, `git branch --show-current`, and `git worktree list --porcelain` in the assigned worktree. Stop before editing on a branch/path/owner mismatch. This is the only active implementation session assigned to #15.
3. Confirm explicit authorization and no native blockers from GitHub. Implement all of #15's acceptance criteria and runtime scenarios, not merely a scaffold.

The original planning checkout is `/Users/sanketsingh/Desktop/alchemy/bibi`. Its untracked `CONTEXT.md`, local spec/planning notes, and `tasks/` belong to that planning checkout and were deliberately left untouched when creating the dedicated worktree. You may read them for context, but do not edit that checkout or sweep its untracked files into implementation commits. GitHub is authoritative for the full ticket/spec.

Domain vocabulary: App discovery finds App Store apps without classifying them as competitors; Keyword search returns limited matches; App-name search requires explicit confirmation but is outside #15's screen scope; Storefront means a country's App Store catalog/ratings, not review language or global data.

## Scope and boundaries

Build local keyword discovery end to end: separate Next.js frontend and FastAPI backend, safe normalized listing contract, shared supported-storefront catalog, explicit submission, real Apple software search, ordered results, US-scoped result screen, initial/loading/results/empty/validation/rate-limit/upstream-failure states, stale-response protection, manual retry, fetch-time/cache indicators, and no persisted browser search state.

The first usable search must already enforce the rolling 10-dispatches/60-second process budget and 8-second overall Apple deadline, counting failed attempts and providing the specified error/Retry-After semantics. Do not add automatic retries, fake fallback data, queues, stale fallback, a database, AI, or direct browser Apple Search calls. Preserve the existing informational landing page.

Return the complete parent-specified normalized API result contract now. Additional metadata/copy UI belongs to #16; app-name confirmation to #17; the country-picker interaction to #18; real metadata cache and identical-request sharing to #19. Until #19, uncached successful searches truthfully return `cached=false`. Do not implement later tickets in this session.

## Required verification

These are ticket commands, not existing passing results. Establish dependencies/runtime documentation with the implementation.

| Action | Working directory | Command |
| --- | --- | --- |
| Behavioral API suite | Assigned worktree's `backend/` | `python -m pytest` |
| Production frontend build | Assigned worktree's `frontend/` | `npm run build` |
| Single-worker loopback API | Assigned worktree's `backend/` | `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1` |
| Loopback frontend | Assigned worktree's `frontend/` | `npm run dev -- --hostname 127.0.0.1 --port 3000` |
| Live API smoke | Assigned worktree root | `curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/search?q=adhd%20planner&country=us&limit=50'` |

Use one real FastAPI pytest/HTTPX test seam, controlling Apple transport and time rather than replacing the search service with an echo mock. Cover the ticket's query/country/limit boundaries, normalization/filter/dedup/null/safe-link behavior, successful empty versus malformed upstream behavior, rolling budget, timeout/failure/429 mappings, and absence of automatic retries. No per-helper or UI unit-test seam is required.

Open the actual browser screen and exercise Search and Enter, no search while typing, populated live results, safe original listing links, late-response protection, and reload reset. Through the same real application path, use controlled upstream outcomes to demonstrate empty/validation/rate-limit/failure/timeout states and retrying the submitted phrase rather than a new draft. Never add a production fake-data endpoint. Tests/build alone are not runtime proof; a live failure or zero result does not prove populated behavior.

## Completion evidence and next gate

Record exact commands, working directories, observed test/build/runtime results, and acceptance-criterion evidence on issue #15. Report blockers honestly. Update required startup/verification documentation within this ticket's branch. Request the user's acceptance of #15 and separate authorization for any commit/merge/close; do not mark later tickets ready to execute based solely on this issue being closed. End this session after #15's work; subsequent tickets each require their own fresh default-model session and exact assigned worktree once dependencies are accepted and integrated.
