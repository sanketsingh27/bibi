# App Store Search — Planning Notes

Status: all five tickets #15–#19 are implemented, tested, explicitly accepted, integrated into local `main` at `3df94ac`, and closed. Each original implementation used a distinct fresh default-model session/worktree. Final main verification: 78 API tests passed, production build passed, live API HTTP 200 and independent production-browser combined smoke passed. Local production app: http://127.0.0.1:3000. No push or public deployment occurred; parent #14 remains open and unchanged.

## Confirmed decisions

- The feature must work in a Next.js web UI.
- FastAPI implements search and owns calls to Apple. LangChain and LangGraph are not required on the search path.
- The intended audience is private, local-only use, not an online deployment.
- Inputs must support app names and keywords. App ID and App Store URL input are not part of the confirmed input scope.
- Competitor classification and competitor selection are not part of the current focus.
- The user explicitly chooses Keyword or App name mode; Bibi does not infer intent from the text.
- Keyword mode displays Apple's returned matches, up to 50, in Apple's returned order. It does not claim exhaustive App Store coverage.
- App-name mode displays matching names and developers for user confirmation, then displays only the chosen app. It does not automatically choose Apple's first result.
- An app-name search with no matching app reports that outcome rather than substituting another app.
- Keep a country picker with United States (`us`) as the default storefront. Never silently fall back to another country.
- Changing storefront clears the confirmed app and reruns the last submitted search in the new storefront, not any unfinished text currently being typed.
- Search runs only through the Search button or Enter, never while typing. Text input is limited to 2–100 characters.
- No saved search history, research selections, accounts, or database. Search results and the confirmed app are page-session state and are not restored after a reload.

## Local infrastructure

- Run a single FastAPI worker. This version is local-only, not a multi-worker or public-service deployment.
- Cache search metadata in memory for 24 hours; cache contents disappear on backend restart. Storefront and search parameters are part of the cache key.
- Identical concurrent searches share one pending Apple request.
- Allow at most 10 upstream requests per minute across this backend process, with an 8-second timeout per Apple request.
- When the budget is exhausted or Apple is unavailable, show an explicit error and a Retry control. Retry is user-triggered; there are no automatic retries, stale-result fallbacks, or background queues.
- Do not introduce Redis, distributed locks, or an agent framework for search. They add infrastructure without serving the agreed single-process use case.

## Search-only boundary

The current scope stops at finding apps and confirming an intended app in App name mode. Competitor classification, bulk app selection, review collection, review analysis, and research persistence are outside this phase.

The original result metadata remains the basis for the specification: app icon where available, name, developer, average rating, rating count, category, copyable numeric Apple app ID, and original App Store link. Missing ratings must not become zero; rating counts must not be described as written-review counts. Apple artwork usage must follow applicable terms; private use does not itself establish compliance.

## Verified upstream facts

Apple documents text search using `term`, with software results selected through `media` and `entity`. It does not document a switch that distinguishes the user's app-name intent from keyword intent, or an exact software-title search guarantee. ID lookup is a separate operation.

Apple documents `limit` from 1 to 200 and no general search-result pagination parameter. A keyword result list must not be described as the complete App Store catalog.

Source: [Apple iTunes Search API](https://performance-partners.apple.com/search-api), accessed 2026-10-21.

### Live observation

A request on 2026-10-21 to [Apple Search for Tiimo in India, limit 5](https://itunes.apple.com/search?term=Tiimo&media=software&entity=software&country=in&limit=5&lang=en_us) returned five apps:

- `1480220328` — Tiimo: Daily To-Do List — tiimo
- `1499198946` — Structured: Daily Planner Todo — unorderly GmbH
- `1438388363` — Habit Tracker — InnerGrow
- `626144601` — TickTick:To-Do List & Calendar — Appest Limited
- `1632352471` — Routine Planner - Daily Tasks — ToolStyle

This demonstrates that a known app-name query can also return other apps and that the listing title need not exactly equal the query. It does not establish that the intended app is always first.

The Python HTTPS attempt failed because its local certificate trust chain was unavailable. The request above succeeded using system `curl` with certificate verification enabled.

### US storefront smoke — 2026-10-22

Live requests used `country=us`, `media=software`, `entity=software`, `limit=50`, and `lang=en_us`, with system `curl`, certificate verification enabled, and an 8-second timeout.

| Query | Returned records | Invalid numeric app IDs | Non-software records |
| --- | ---: | ---: | ---: |
| `Tiimo` | 40 | 0 | 0 |
| `adhd planner` | 45 | 0 | 0 |

Sources: [Tiimo request](https://itunes.apple.com/search?term=Tiimo&media=software&entity=software&country=us&limit=50&lang=en_us) and [keyword request](https://itunes.apple.com/search?term=adhd+planner&media=software&entity=software&country=us&limit=50&lang=en_us). These checks exercise Apple directly, not a Bibi implementation; no search application has been implemented in this planning session.

## Design confirmation

The user requested specification synthesis through `/to-spec` after reviewing the consolidated design, then explicitly approved the proposed testing approach with “Approve testing approach.” The approved approach is one automated boundary at the real FastAPI HTTP API using pytest and HTTPX, with controlled Apple responses/time, plus separate browser runtime verification of the real Next.js → FastAPI → Apple path.

The specification is published at [GitHub issue #14](https://github.com/sanketsingh27/bibi/issues/14), with a local copy in `app-store-search-spec.md` beside this document. Its seven required sections and 50 numbered user stories were checked; the published body was fetched and verified against the local copy, and the `ready-for-agent` label was verified. That label does not authorize implementation.

In the ticket-planning conversation, the user selected “Approve spec as written,” then “Approve and publish five tickets.” Tickets [#15](https://github.com/sanketsingh27/bibi/issues/15), [#16](https://github.com/sanketsingh27/bibi/issues/16), [#17](https://github.com/sanketsingh27/bibi/issues/17), [#18](https://github.com/sanketsingh27/bibi/issues/18), and [#19](https://github.com/sanketsingh27/bibi/issues/19) are published with full contracts, exact issue-scoped branches based on `main`, verified native blocking relationships, and verified `ready-for-agent` labels. All 50 parent stories are assigned. The published ticket index, branch mapping, and verification evidence are in [the implementation plan](../tasks/plan.md). Only #15 is currently unblocked; implementation requires separate authorization and a fresh session. The parent issue was not modified or closed.

The user subsequently authorized implementing and testing all five tickets, each in a different session. Authorization is recorded on #15–#19; it does not waive acceptance or commit/merge/close gates. The registered #15 worktree is `/Users/sanketsingh/Desktop/alchemy/bibi-15-keyword-discovery` on its exact assigned branch, `feature/15-keyword-discovery`, based on `main`. A new OMP session has been launched without model/continuation overrides; the [handoff](../tasks/handoff-15.md) contains the ownership and verification contract. Later tickets must wait for accepted prerequisite changes to be integrated into `main`.

## Original proposal

Source document: `/Users/sanketsingh/Downloads/bibi_app_store_search_mvp.md`.

The decisions above supersede conflicting parts of the source proposal, notably competitor/review actions, the India default, typing debounce, and distributed infrastructure. Optional features from the source are not automatically in scope.
