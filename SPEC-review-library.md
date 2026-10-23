# Spec: Local Review Library

## Problem Statement

Bibi does not yet collect or retain written reviews. Apple's public JSON feed can return real review records, empty pages, errors, and non-contiguous page coverage. A listing's rating count is not the number of written reviews available through that feed. Treating an empty page as the end of all reviews or silently combining storefronts would produce misleading research.

The researcher needs a bounded, cancellable collection process, honest coverage, exact local star filters, and saved research that survives reopening. Those behaviors must work without an AI key and must not automatically rerun paid reports when more evidence is fetched.

## Solution

Add the review-library capability to fetch a mixed-star Review sample for an explicitly selected App Store app and storefront. Target up to 200 reviews initially; offer an explicit target of 500. Scan at most ten distinct page numbers using paced requests, continue past empty intermediate pages, deduplicate source IDs, and preserve partial data on cancellation, rate limits, or failure.

Persist actual samples and their provenance in browser IndexedDB, provide a Saved research list, exact local All stars/one-to-five-star filtering, explicit refresh/deletion, and visible storage failures. Introduce the transient operation API reused by analysis/comparison, without creating a persistent backend research database.

## User Stories

1. As a researcher, I want selecting an app to start a bounded initial review fetch, so that searching the catalog alone does not collect reviews.
2. As a researcher, I want an initial target of 200 mixed-star written reviews, so that the first sample has a predictable upper bound.
3. As a researcher, I want to request a larger target of 500 explicitly, so that additional collection is under my control.
4. As a researcher, I want fetched and requested counts shown separately, so that source shortfalls are visible.
5. As a researcher, I want populated pages after empty pages considered within the bound, so that an empty intermediate response does not discard later evidence.
6. As a researcher, I want the source page gaps recorded, so that the sample is not falsely described as the latest complete collection.
7. As a researcher, I want each source review counted once, so that repeated IDs across pages do not inflate coverage.
8. As a researcher, I want an invalid review record excluded with a visible coverage warning, so that malformed data does not become fabricated evidence.
9. As a researcher, I want an invalid response envelope distinguished from an empty page, so that upstream failures are not presented as success.
10. As a researcher, I want reviews tied to their app ID and storefront, so that samples from different scopes cannot be mixed silently.
11. As a researcher, I want actual progress while fetching is paced, so that a wait is understandable and cancellable.
12. As a researcher, I want cancellation to stop additional page requests and retain completed records, so that stopping an operation does not discard useful data.
13. As a researcher, I want a rate-limited operation to pause with partial data and recovery guidance, so that automatic repeated requests do not worsen the limit.
14. As a researcher, I want explicit resume to reuse completed same-scope work, so that it does not unnecessarily repeat successful source requests.
15. As a researcher, I want a ten-page/request bound, so that an unavailable source cannot lead to an unlimited scan.
16. As a researcher, I want source empty/error states not to imply that the app has no written reviews, so that absence of fetched evidence is interpreted correctly.
17. As a researcher, I want review text, title, stars, update date, and available version stored, so that analysis can link back to the source evidence.
18. As a researcher, I want reviewer names and profile links omitted from normalized research, so that unnecessary personal information is not retained.
19. As a researcher, I want All stars and individual one-to-five-star filters over saved records, so that rating selection is exact and local.
20. As a researcher, I want filter changes not to fetch or analyse again, so that browsing a subset has no hidden network or AI cost.
21. As a researcher, I want filter counts scoped to my saved sample, so that I do not mistake them for all matching App Store reviews.
22. As a researcher, I want saved research listed by app and storefront, so that I can return to a previous investigation.
23. As a researcher, I want reopening saved research to make no automatic refresh or AI request, so that I control new work.
24. As a researcher, I want fetching more reviews to preserve the existing analysis and show its coverage, so that downloading evidence alone does not incur another report charge.
25. As a researcher, I want an explicit Update analysis action after expansion, so that I choose when the larger sample is analysed.
26. As a researcher, I want an explicit Refresh reviews and analyse action, so that refreshing current evidence is deliberate rather than tied to navigation.
27. As a researcher, I want an all-empty or failed refresh to preserve the prior valid snapshot, so that a temporary feed problem does not erase research.
28. As a researcher, I want changed review text or stars to invalidate associated derived data, so that stale embeddings/reports are not silently presented as current.
29. As a researcher, I want deletion to remove the app/storefront's samples and derived reports/indexes, so that deleted evidence is not retained in a hidden index.
30. As a researcher, I want storage/quota failures shown clearly, so that the app never claims an unsaved result is persistent.
31. As a researcher, I want clearing browser storage distinguished from deleting the AI key, so that independent local storage lifetimes are understandable.
32. As a researcher, I want repeated requests for one running intent to share that operation, so that polling or accidental resubmission does not duplicate collection.
33. As a researcher, I want an interrupted backend operation reported honestly after restart, so that a missing process-local job is not mistaken for completion.
34. As a researcher, I want keyboard-operable fetch, filter, cancel, resume, refresh, and deletion controls, so that the library is accessible.

## Implementation Decisions

### Capability and normalized records

- Stable module ID: review-library. Dependency: app-details. It supplies browser research persistence, review-source behavior, and the transient operation coordinator later used by review-analysis and competitor-comparison. It does not depend on an AI key to collect or display reviews.
- Use the parent's AppIdentity, ReviewRecord, ReviewSample, fingerprint, operation, and error contracts. A ReviewRecord includes reviewId, appId, country, nullable title, plain-text text, stars, updatedAt, nullable version, fetchedAt, and an optional safe original Apple link. Do not normalize author names/profile URLs into research records.
- Require an actual source ID, valid one-to-five-star numerical rating, and non-empty review text for a usable written review. Support an entry array or single-entry object when the feed otherwise validates. Do not count feed metadata or an app-description entry as a review. Validate dates and other fields; malformed required records are excluded with coverage warnings rather than converted into invented values.
- A valid metadata-only feed is an empty/unavailable page. A malformed feed envelope, request error, unsafe link, timeout, and rate-limit response are different outcomes. Keep page-level observations rather than collapsing every failure into an empty successful list.
- Deduplicate by app/storefront/source reviewId. Within one collection keep the first usable occurrence in page/source order. An explicit refresh may update a review's substantive fields without increasing its count. Canonical sample fingerprints include identity and sorted IDs/text/stars/source time/version, not only fetch timestamps.

### JSON source and bounded collection

- Use the fixed Apple HTTPS public customer-review JSON URL family with explicit storefront, app ID, page number, and mostrecent order. Construct upstream requests from validated identity/page data; never accept arbitrary caller URLs, scrape App Store HTML, or silently switch to an XML/paid/authenticated source.
- Initial targetCount is 200; explicit expansion targetCount is 500. Other requested targets are validation errors for this feature. Neither target is a promise of that many available reviews. Star-filtered fetching is not assumed: collect mixed-star records, then apply numerical filters locally.
- For a fresh requested fetch, attempt page numbers 1 through 10 in order, at most once each, stopping earlier at the unique-record target, cancellation, or a pause/error boundary. An empty intermediate page does not terminate the scan. Do not add repeated URL-spelling retries or an unbounded walk of source links. Retain ten as an application safety bound, not an Apple-guaranteed page count or total.
- Expansion/resume includes validated prior same-scope sample/page observations and reuses existing records. Dispatch only necessary unattempted pages within the same ten-page horizon; skip duplicates and already successful page work. If the prior ten-page horizon is exhausted or remains gapped, explain the shortfall instead of looping or switching countries. Explicit refresh may start a new bounded pass and revisit prior pages.
- Share the existing ten-dispatches-per-rolling-60-seconds Apple budget across search, lookup, and review work, counting failed attempts, with eight-second request deadlines. A cache/operation poll is not a new Apple dispatch. Pace requests through the budget; do not launch ten simultaneous page requests as a claim to avoid rate limits.
- Show actual progress during source waits and local budget waits. Honor Retry-After when provided. Stop further dispatches on upstream rate limiting, preserve valid records/page observations, and expose a user-triggered resume/retry at or after the wait. No automatic retry loop is added.
- Return partial records and truthful warnings on bounded timeout/error/cancellation where data exists. A zero-record collection is unavailable, not proof of zero App Store reviews. Show targetReached independently of coverage: even reaching 200 does not turn a gapped or limited public-feed sample into complete App Store coverage.
- Never merge storefronts to reach a target. Requested URL territory is the sample scope; do not infer a reviewer's residence from it. A returned original link must remain a safe Apple HTTPS link and match the expected identity where the source supplies that identity.

### Operation lifecycle

- POST /api/v1/apps/{appId}/review-fetches accepts requestId, country, targetCount, and optional existing ReviewSample for expansion/resume. Validate browser-supplied records and page observations; they are not implicitly trusted because they were saved locally. Return HTTP 202 with the operation descriptor, not a fabricated completed sample.
- The shared operation descriptor contains operationId, kind, status, scope, and actual progress, with terminal result or safe error. Kinds are review-fetch, analysis, suggestions, comparison, and embedding-setup. States are queued, running, succeeded, partial, failed, and cancelled. The result's review availability/coverage can still be partial/unavailable independently of HTTP transport success.
- GET /api/v1/operations/{operationId} polls actual state without source dispatch. POST /api/v1/operations/{operationId}/cancel cooperatively stops additional work and retains completed partial data. Poll/cancel access uses the parent's local request protections, and operation IDs are unguessable.
- Keep operation state in bounded backend memory only. Identical requestId and payload join/replay within the running process; changed payload under the same ID returns conflict. Retain completed descriptors for one hour. Bound active work, support cancellation during pacing, and do not retain unbounded large result histories in backend memory.
- No durable exactly-once claim survives process restart. A lost operation is interrupted/unknown; the browser preserves its last completed snapshot and asks for explicit recovery. Later paid-work consumers must not automatically re-submit an uncertain operation or claim that cancellation reverses a sent charge.
- View updates carry app/storefront/request identity. Ignore late completions for a superseded view and never save an old result over a newer explicitly selected scope.

### IndexedDB and user controls

- IndexedDB is the authoritative persistent store for listing snapshots, raw normalized review samples, derived local vectors, reports, and provenance. There is no backend research database or persistent graph checkpoint store. The backend accepts validated snapshots needed for operations after reopening.
- Retain historical sample versions while a saved report still cites them. An evidence link includes the app/storefront, sample fingerprint, and source review ID, so refreshing an edited review cannot silently change an older report's supporting text. Deletion removes all versions for that app/storefront and their dependent evidence; routine refresh must not orphan historical citations.
- Scope records and derived associations by app/storefront/fingerprint and model revision where relevant. Sample replacement and derived-state updates must not leave partial associations claiming nonexistent evidence. Handle schema upgrades without silently dropping existing research; if migration/storage fails, report it and preserve recoverable old data.
- Provide Saved research navigation grouped by app/storefront. Reopening, switching tabs, filtering stars, or changing the configured generative model does not automatically fetch or rerun old reports. Saved data is labelled with its actual source times and sample/report coverage.
- Star filters offer All stars or one integer from 1 to 5 and run over saved records. Filter count is not the total matching App Store population. Render review content as plain text, expose original evidence links safely, and preserve source identity in report deep links.
- Initial collection can trigger the parent's initial analysis after data and prerequisites are ready. Explicit fetching-more preserves the prior report and labels analysed-versus-saved count. Only Update analysis or Analyse filtered reviews starts that new paid scope. Refresh reviews and analyse is an explicit combined intent; if refresh cannot obtain a replacement sample, retain the prior sample/report and disclose the failed/unavailable attempt rather than calling an empty result fresh evidence.
- Delete research removes that app/storefront's samples, chunks/vectors, analyses, and stored comparison associations that rely on deleted evidence. Other apps/storefronts and the separately stored OpenRouter key remain. Do not leave a comparison appearing current with unresolvable deleted source IDs.
- Storage failures/quota denial are visible. A view may show completed data still in memory with an explicit not-saved state, but it must not claim persistence or silently upload to a fallback store. Clearing browser data can remove research while the OS key remains; explain that distinction.
- Fetch targets, source waits, progress, cancellation, resume, filters, refresh, and deletion must be labelled, keyboard-operable, and available on narrow screens. Do not add a general research chat, export, or account interface.

## Testing Decisions

The user approved the existing real FastAPI/pytest/HTTPX boundary as the primary automated seam. Prior art is `backend/tests/test_search.py`, with controlled Apple HTTP responses and time while routing/services execute for real. Extend it for collection and operations; do not add implementation-layout, helper/wiring, incidental-wording, or source-text tests.

Permanent regression scenarios must include:

- Actual review records versus metadata/app entries; single-entry and array shapes; malformed required fields; invalid rating/text/IDs; duplicate IDs and updated reviews without inflated counts.
- Empty page 2 and page 3 followed by populated page 4, with correct coverage warnings; bounds at 200, 500, and ten pages; exhausting the page horizon before the target.
- App/storefront isolation, rejected arbitrary upstream links/unsupported parameters, and no country substitution to fill a shortfall.
- Shared rolling-budget boundaries, failures consuming dispatch budget, cancellation while waiting/between pages, rate-limited partial results, no automatic retry, and explicit resume without repeated successful pages.
- Actual operation progress and terminal results, stable-intent replay versus payload conflict, unknown operation after process loss, and preservation of completed prior samples/reports when refreshing fails.

Browser persistence/filtering is verified at runtime, not claimed covered by API tests:

1. Start the actual local app, select an app, fetch a real public sample, and observe actual target/count/gaps. Save, reload, and reopen through Saved research without a fresh source or AI call.
2. Select three stars and verify every displayed record has the stored numerical rating. Return to All stars and observe the original saved sample count without another source request. Use a controlled sample when live source data cannot cover every rating.
3. Fetch more explicitly. Observe progress/cancellation and 500 as a target, not a guarantee. Confirm the previous report remains labelled with its earlier coverage and no inference runs until Update analysis.
4. Through a temporary controlled-upstream runner, exercise page gaps, malformed data, timeouts, rate limits/resume, and cancellation. Inspect actual page dispatches and preserved results; no production fixture routes or fake review fallback.
5. Deny/fill browser storage or simulate a transaction failure through browser tooling. Confirm the app reports not-saved/migration errors rather than success. Delete one app/storefront and verify dependent records disappear while another app and the key remain.

Commands: backend virtual environment active, `python -m pytest`; API runtime `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`; frontend `npm run build` and `npm run start -- --hostname 127.0.0.1 --port 3000`. Inspect http://127.0.0.1:3000 with actual browser/network/IndexedDB tooling. No new frontend test framework is proposed.

During planning, source probes obtained actual Apple Support US and Notion US/CA review records and exercised exact local filtering. That is source feasibility evidence, not a passing implementation test or evidence of reliable 500-review coverage.

## Out of Scope

- Paid review-data sources, App Store HTML scraping, XML fallback, private/authenticated Apple endpoints, and arbitrary upstream URLs.
- Guaranteed 200/500 matching-star reviews, complete/global/latest-contiguous coverage, inferring no reviews from an empty feed, or silently mixing storefronts.
- Backend SQLite/Drizzle/research databases, remote synchronization, accounts, exports, graph checkpoint databases, and remote embedding/vector services.
- Automatic analysis after fetching more, changing filters/tabs/model, or reopening; automatic retry loops, unbounded page scans, and durable exactly-once claims.
- AI report generation inside this capability, semantic star filtering, permanent production fixture endpoints, or a new UI test framework.

## Further Notes

Parent specification: [#20 — Local app details, review analysis, and competitor comparison](https://github.com/sanketsingh27/bibi/issues/20).

Published module specification: [#23](https://github.com/sanketsingh27/bibi/issues/23). Blocked by the [app-details specification #22](https://github.com/sanketsingh27/bibi/issues/22) in the capability dependency graph; this is not an implementation ticket.

Module ID: review-library. Depends on app-details; supplies the transient operation and saved-sample contracts used by review-analysis. The browser persistence boundary is intentional and must not be replaced by a server database during implementation for convenience.

The user confirmed design/source limits/200-and-500 targets/local star filtering and selected **Approve map and tests**. This specification remains pending user approval and is not an implementation ticket or authorization. Future tickets require explicit tests/runtime scenarios, prerequisites, accepted dependencies, assigned branches/worktrees, and fresh-session authorization.

Source observations: [Apple Support US page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1130498044/sortby=mostrecent/json) returned 50 written reviews; [Notion US page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1232780281/sortby=mostrecent/json) and [page 4](https://itunes.apple.com/us/rss/customerreviews/page=4/id=1232780281/sortby=mostrecent/json) returned distinct records while pages 2–3 were empty. [Notion Canada](https://itunes.apple.com/ca/rss/customerreviews/id=1232780281/sortby=mostrecent/json) returned a distinct sample. These observations justify gaps/partial states, not an availability guarantee or legal right to persist/reuse content.

Apple's separate [App Store Connect review API](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps-_id_-customerreviews) documents authenticated rating filters for accessible apps; those parameters must not be projected onto the public feed. Closed [#7](https://github.com/sanketsingh27/bibi/issues/7) describes historical SQLite-based research, not the current implementation seam.

Before an affected implementation ticket is marked ready, verify applicable source terms/permission for the planned persistent reuse and external AI processing. Public accessibility and user design approval alone do not establish those rights. No app code, database, tests, model download, or paid inference was changed/run for this specification.
