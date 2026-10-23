## Problem Statement

A founder or product manager wants to find Apple App Store apps from a market keyword or a known app name, inspect enough listing information to identify the relevant apps, and open the original listings. Searching by a known name can still return many unrelated apps; choosing the first result silently risks identifying the wrong product. Search results and rating metrics also depend on the country storefront.

Bibi's current checkout contains an informational landing page, not a working search application. The user needs a private, local web interface for app discovery before introducing competitor research, review collection, or AI analysis.

## Solution

Build a local Next.js web application backed by FastAPI. The user explicitly chooses Keyword or App name mode, selects a storefront, enters a search phrase, and submits with Search or Enter. United States is the default storefront. Typing alone never searches.

Keyword mode displays up to 50 normalized matches in Apple's returned order. App-name mode presents matching names and developers for explicit confirmation, then displays only the confirmed app. Neither mode claims exhaustive App Store coverage or automatically classifies matches as competitors.

Show listing metadata, a copyable numeric Apple app ID, and the original App Store link. FastAPI owns Apple API requests, a 24-hour in-memory metadata cache, identical-request sharing, and a conservative upstream request budget. The app runs locally without accounts, a database, saved searches, or AI orchestration.

## User Stories

1. As a private researcher, I want to open Bibi locally in my browser, so that I can discover apps without deploying a public service.
2. As a researcher, I want to choose Keyword or App name mode explicitly, so that Bibi does not guess my intent from ambiguous text such as Calm.
3. As a researcher, I want to search a market phrase such as ADHD planner, so that I can inspect relevant App Store matches.
4. As a researcher, I want to search a known app name such as Tiimo, so that I can find the intended listing even when its full title contains extra words.
5. As a researcher, I want to submit using a Search button, so that I control when a request is sent.
6. As a keyboard user, I want Enter to submit the search form, so that I do not need a pointer to search.
7. As a researcher, I want typing and editing to remain local until submission, so that incomplete phrases do not consume upstream requests.
8. As a researcher, I want invalid or too-short input explained before searching, so that I can correct it without wasting an Apple request.
9. As a researcher, I want harmless surrounding and repeated whitespace normalized, so that equivalent phrases behave consistently.
10. As a researcher, I want United States selected initially, so that the first search uses my agreed default storefront.
11. As a researcher, I want an editable country picker with readable country names, so that I can search another supported App Store storefront.
12. As a researcher, I want the active storefront clearly displayed with results, so that I do not mistake one country's listing metrics for global data.
13. As a researcher, I want changing storefront to rerun my last submitted phrase, so that the displayed results reflect the new storefront.
14. As a researcher, I want an unfinished edit excluded from an automatic storefront rerun, so that changing country does not accidentally submit a draft.
15. As a researcher, I want an earlier confirmed app cleared when I change storefront or submit another search, so that I cannot confuse it with the current result set.
16. As a researcher, I want an unavailable app or empty search represented honestly, so that Bibi does not silently substitute another storefront or product.
17. As a keyword-search user, I want to see up to 50 returned matches, so that I can browse useful alternatives without an unnecessarily large response.
18. As a keyword-search user, I want Apple's returned order preserved, so that Bibi does not introduce an unexplained ranking.
19. As a keyword-search user, I want the interface to explain that results are limited search matches, so that I do not treat them as the entire App Store catalog.
20. As an app-name-search user, I want to compare candidate titles and developers, so that similar names do not cause me to choose the wrong app.
21. As an app-name-search user, I want to confirm the intended listing myself, so that Bibi never silently assumes the first result is correct.
22. As an app-name-search user, I want only the confirmed app shown after selection, so that I can focus on that product.
23. As an app-name-search user, I want to return to the candidate list, so that I can correct a mistaken confirmation without another Apple request.
24. As an app-name-search user, I want an honest no-match state when the intended app is absent, so that another app is not presented as an exact match.
25. As a researcher, I want each result to show its app name and developer, so that I can identify and disambiguate listings.
26. As a researcher, I want an app icon where available and permitted, so that familiar apps are easier to recognize.
27. As a researcher, I want the app category displayed, so that I can assess relevance beyond the title alone.
28. As a researcher, I want average rating and rating count displayed separately, so that I understand the listing's rating metrics.
29. As a researcher, I want missing ratings rendered as unavailable, so that missing data is not misrepresented as a zero-star score.
30. As a researcher, I want rating counts labelled as ratings rather than reviews, so that I do not infer a written-review count Apple did not provide.
31. As a researcher, I want the numeric Apple app ID visible and copyable, so that I can use the stable identifier outside this search screen.
32. As a researcher, I want to open the original App Store listing, so that I can inspect Apple's source information directly.
33. As a researcher, I want missing optional listing metadata handled safely, so that an incomplete listing does not break the result view.
34. As a researcher, I want duplicate Apple records collapsed, so that the same app is not presented repeatedly in one result set.
35. As a researcher, I want non-software records excluded, so that the screen remains focused on apps.
36. As a researcher, I want distinct initial, loading, results, and empty states, so that I understand what Bibi is doing.
37. As a researcher, I want late responses from older searches ignored, so that they cannot replace the results for my current submitted search and storefront.
38. As a researcher, I want repeated searches to reuse fresh cached metadata, so that results load without unnecessary Apple requests.
39. As a researcher, I want the metadata fetch time and cache status visible, so that I can judge the freshness of the listing information.
40. As a researcher, I want searches in different storefronts kept separate in the cache, so that their availability and ratings are not mixed.
41. As a researcher using more than one tab, I want identical simultaneous searches to share one Apple request, so that duplicate activity does not consume the upstream budget unnecessarily.
42. As a researcher, I want an explicit rate-limit error and a manual retry path, so that I know when the service cannot make another Apple request yet.
43. As a researcher, I want upstream timeouts and failures distinguished from no matches, so that a service failure is not mistaken for an empty catalog result.
44. As a researcher, I want retries to happen only when I request them, so that Bibi does not generate hidden traffic or background work.
45. As a researcher, I want expired metadata refreshed instead of silently served as fresh, so that the displayed fetch time remains truthful.
46. As a researcher, I want reloading the page to clear my prior search and confirmed app, so that this phase does not create a saved workspace.
47. As a local operator, I want restarting FastAPI to clear its cache, so that no database or persistent cache service is required.
48. As a local operator, I want all Apple Search API requests owned by FastAPI, so that one process controls caching, request sharing, timeouts, and the upstream budget.
49. As a local operator, I want a single-worker local setup with documented startup and verification commands, so that I can run the feature without Redis, distributed locks, or agent infrastructure.
50. As a researcher, I want searching and confirming an app to stop at listing discovery, so that no competitor set, review collection, or AI analysis starts without a separately approved feature.

## Implementation Decisions

### Application boundaries and local operation

- Add a Next.js search application and a FastAPI backend without replacing or changing the existing informational landing page.
- The browser calls Bibi's API for search and storefront options; FastAPI calls Apple. Direct image loading and opening an App Store listing are distinct from browser calls to Apple's Search or Lookup APIs.
- Run the frontend and one FastAPI worker on loopback interfaces. Document the local start commands, required runtimes, working directories, and expected browser address as part of implementation. A public or multi-worker deployment is unsupported by this spec.
- Use one search pipeline for both modes. Mode determines browser presentation and confirmation behavior, not a separate Apple search algorithm or an LLM classification step.
- Keep the implementation conventional: an Apple HTTP adapter, a search service owning normalization/cache/in-flight requests/budget, the FastAPI HTTP boundary, and the Next.js screen. Do not introduce separate unit-test seams solely for each module.
- No database schema is introduced. Page state is not saved to local storage, session storage, a saved-search URL, or server-side user storage. Backend cached listing metadata is shared transient infrastructure, not persisted user search history.

### Storefront catalog

- Maintain a static allowlisted catalog of supported App Store country storefronts, using lowercase ISO 3166-1 alpha-2 codes and readable names. United States (`us`) is the default; India (`in`) must also be selectable.
- Derive the catalog from Apple's published App Store availability rather than treating every ISO country code as automatically supported. The authoritative availability reference is linked in Further Notes. Do not scrape Apple or fetch storefront availability during each search.
- Expose the catalog through `GET /api/v1/apps/storefronts`, returning `defaultCountry` and a `storefronts` list whose entries contain `code` and `name`. This endpoint makes no upstream request and does not consume the Apple budget.
- Both the picker and backend validation use this catalog; an unsupported code is a validation error, never a request to a default or substitute storefront.

### Search API contract

- Provide `GET /api/v1/apps/search` with query parameters `q`, `country`, and `limit`.
- `q` is required. Trim and collapse whitespace, then require 2–100 characters. Preserve the user's entered phrase in browser state for display; normalization does not infer intent or rewrite words.
- `country` defaults to `us`. Trim and lowercase it, then validate against the storefront catalog.
- `limit` is an integer from 1 through 50 and defaults to 50. The UI requests 50; the backend does not accept an undocumented pagination or offset parameter as a feature.
- Both modes use Apple's text Search endpoint with the normalized phrase, selected country, fixed `media=software`, `entity=software`, and `lang=en_us`. Known-name searches are not exact-match lookups. App ID and URL detection, Lookup API requests, and bundle-ID lookup are excluded.
- Return HTTP 200 for a valid successful search, including a genuinely empty result set. The response contains normalized `query`, lowercase `country`, UTC ISO-8601 `fetchedAt`, boolean `cached`, and `results`.
- `fetchedAt` is when metadata was fetched from Apple, not when a cached response was returned. `cached` is true when this request was satisfied from an existing fresh cache entry; a caller joining a pending upstream request is not a cache hit.
- Each normalized result contains `appId`, `name`, `developer`, `iconUrl`, `averageRating`, `ratingCount`, `category`, `storeUrl`, and `country`. `appId` is a positive JSON integer representable safely in the frontend; `country` is the selected storefront. Missing optional display values are null, not fabricated values.
- Map `trackId`, `trackName`, `artistName`, `artworkUrl100` with `artworkUrl60` fallback, `averageUserRating`, `userRatingCount`, `primaryGenreName`, and `trackViewUrl` to the corresponding normalized fields.
- Validate the Apple response envelope and field types before use. A malformed response is an upstream failure, not a successful no-match response. Filter non-software records and records without a valid app ID; deduplicate by app ID, keeping the first usable record and preserving remaining order. Return no more than the requested limit.
- Treat missing or invalid optional ratings as unavailable. A valid zero rating count remains zero; no rating is inferred from the count. Do not calculate a review average, invent download/revenue metrics, or sort missing ratings as zero.
- Treat listing text as plain text, not HTML. Accept only safe HTTPS URLs for artwork and original Apple listing links; unsafe or malformed optional URLs become unavailable rather than executable links. Do not accept an arbitrary upstream URL from a caller.
- Browser-visible search responses are not persisted through HTTP/Next.js caching as a second cache layer. FastAPI owns the agreed metadata freshness policy.

### In-memory cache and single-flight behavior

- Cache successful normalized results, including successful empty results, for 24 hours from a successful fetch. Use normalized phrase, country, limit, and the fixed upstream search parameters as the effective cache identity. The two UI modes may share identical underlying search results.
- Normalize whitespace for identity without adding case-folding or semantic query rewriting. Different storefronts and limits do not share entries.
- Check the cache before allocating a new upstream request or consuming budget. Expired entries are misses and must not be returned as a fallback.
- Concurrent requests with the same uncached key join one in-flight operation. Its success or failure reaches all waiting callers; completion or failure clears the in-flight entry so a later manual retry can proceed.
- Successful cached data is kept only in the running backend's memory. Do not cache exceptions, rate-limit responses, or failed searches. Restarting the backend resets the cache, budget state, and in-flight state.
- This guarantee applies to the agreed single worker only; no distributed guarantee is claimed.

### Upstream budget, timeout, and errors

- Permit at most 10 new Apple Search requests in any rolling 60-second window across the backend process. Count each dispatched attempt, including failed attempts. Reserve a slot before dispatch, not after the response.
- Fresh cache hits, catalog requests, and callers joining an existing in-flight search do not consume additional slots. Budget exhaustion fails immediately rather than queueing the request.
- Apply an 8-second overall deadline to the Apple operation, including reading the response, rather than allowing separate phases to extend the total indefinitely. Do not disable TLS verification.
- No automatic retries, exponential backoff loop, stale fallback, job queue, or polling is introduced. Retry is an explicit user action through the same validated API and remains subject to the budget.
- Use one structured error envelope containing `error.code` and a safe human-readable `error.message`. Do not expose raw exceptions or arbitrary Apple response bodies to the browser.
- Use HTTP 422 with `VALIDATION_ERROR` for invalid input; no Apple request is made.
- Use HTTP 429 with `SEARCH_RATE_LIMITED` when the local rolling budget is exhausted, with a `Retry-After` value indicating the next eligible attempt.
- Use HTTP 429 with `UPSTREAM_RATE_LIMITED` when Apple responds with 429. Preserve a valid Apple `Retry-After` indication when present; do not invent a fixed Apple reset period when it is absent.
- Use HTTP 504 with `UPSTREAM_TIMEOUT` for the deadline, and HTTP 502 with `UPSTREAM_ERROR` for other Apple/network failures, non-success responses, or malformed response envelopes. These are never rendered as no matches.

### Screen behavior

- Start with an empty search input, an explanatory empty state, explicit Keyword/App name controls, and the US storefront selected. Do not run a search on first load.
- Both a labelled Search button and Enter submit the same form behavior. Typing, focusing, changing between search modes, and confirming a result do not themselves call Apple.
- Maintain separate draft text and last-submitted search identity. A new submission clears the confirmed app. Changing mode clears the confirmed app and returns to the submitted result candidates if present; its next submission uses the chosen mode.
- Changing country clears the confirmed app and reruns the last submitted phrase in the newly selected storefront. With no submitted search, changing country only changes the picker. Never submit unfinished draft text through this action.
- Distinguish initial, loading, populated, no-match, invalid-input, rate-limited, and upstream-failure states. Clearly identify the query and storefront belonging to displayed results. A late response must not replace a newer submitted search or country selection.
- In Keyword mode, show all normalized returned matches up to the cap. Do not add competitor checkboxes, Select top 10, bulk research actions, pagination, rating sorting, or an exact-name ranking boost.
- In App name mode, show candidate names and developers with an explicit confirmation action, including when only one candidate is returned. Confirmation displays only that app. Returning to the candidate list is a local action using the already fetched results, not another search. Never label the first result as an automatically verified exact match.
- Show available icons, names, developers, category, average rating, rating count, copyable numeric app ID, and original App Store links. Clearly mark unavailable metadata. Copy success or failure must be observable without falsely reporting a successful copy.
- Display metadata fetch time and whether the response was cached. Label the count as displayed search results, not a full catalog total. Explain that rating metrics belong to the selected storefront and that rating count is not written-review count.
- App artwork must follow Apple's applicable promotional-content conditions, including a proximate approved App Store badge linked to the corresponding listing. Store only metadata/URLs in the search cache, not downloaded artwork files. Do not infer legal approval from the tool being private.
- Keep the controls keyboard-operable and labelled; expose loading/error/result status accessibly. Opening a listing must not start review collection or save research.
- Retrying repeats the failed submitted search and storefront, not an unsubmitted draft. Reloading restores the initial empty state and US default, although the backend metadata cache may still be warm.

## Testing Decisions

### Approved boundary and prior art

- The user explicitly approved the following approach: one automated behavioral boundary at the real FastAPI HTTP API, using pytest and HTTPX, plus separate browser runtime verification of the real Next.js → FastAPI → Apple path.
- There is no application/backend test suite in this checkout to extend. The existing informational landing page has build/dev/deploy commands but no behavioral test runner. Historical issue #7 mentions Vitest in an older implementation; that code and test seam are absent here and must not be claimed as reusable prior art.
- Exercise the real FastAPI routing, validation, normalization, cache, in-flight coordination, and budget together. Control Apple's HTTP boundary with representative saved response fixtures and control time for deterministic expiry/budget scenarios. Do not replace the search service with a mock that merely echoes expected responses.
- A good permanent test demonstrates a consumer-visible behavior, boundary, error, precedence rule, or transition that could plausibly regress. Do not assert implementation layout, helper names, exact incidental wording, copied fixtures, mock forwarding, or timing-sensitive sleep durations. Do not create separate helper or UI unit suites to inflate test counts.

### Automated API scenarios

- Valid app-name and keyword phrases return the normalized contract and preserve upstream order; both modes can consume the same endpoint.
- Whitespace normalization and the 2/100-character boundaries work; unsupported countries, missing/invalid query text, and non-integer or out-of-range limits fail without upstream traffic.
- The storefront catalog supplies the default US choice and includes India; its allowlist and search validation agree. Changing storefront changes the upstream country and cache identity.
- Representative payloads exercise duplicate IDs, non-software results, invalid/missing IDs, missing optional metadata, null versus genuine zero rating counts, and malformed/unsafe optional values. Assertions concern usable output and explicit failure behavior, not a particular parser implementation.
- A successful empty response remains distinct from an invalid JSON/envelope response, an Apple error, or a timeout.
- A fresh repeated query avoids another Apple request and retains the original fetch timestamp. Expiry at the 24-hour boundary triggers a new request; no expired entry is returned after a failed refresh.
- Different countries and limits are isolated; equivalent whitespace forms share their cache identity. Successful empty results can be cached; failures cannot.
- Concurrent identical misses cause one upstream request and yield the same data. A shared failure reaches its callers, and a later retry can make a new attempt instead of being stuck on a failed in-flight operation.
- The first 10 distinct uncached dispatches inside a rolling minute may reach Apple; the next is rejected before dispatch with a retry indication. Advancing controlled time admits the next eligible request. Cache hits and joined in-flight requests remain usable without consuming a slot, including when the budget is exhausted.
- Apple 429, other upstream failures, malformed envelopes, and timeout map to the documented error contract. Failed attempts consume a slot, no automatic second attempt occurs, and recovery requires a new caller request.
- API tests remain deterministic, offline, isolated between test cases, and safe for the complete suite. Use events/barriers for concurrency and a controllable clock for TTL/budget checks, not long sleeps or dependence on Apple's changing catalog.

### Runtime acceptance

- Implementation must document exact local startup commands and working directories, provide `python -m pytest` for the backend behavioral suite, and provide frontend `npm run build` and `npm run dev` commands. These are required implementation deliverables, not commands claimed to work in the current checkout.
- Run the automated API suite and production frontend build, then open the actual local application in a browser. Tests or compilation alone do not prove the feature complete.
- On a fresh load, observe the blank input and US default. Type without submitting and verify that no search API or Apple Search request is issued. Submit `adhd planner` through Search and through Enter in separate checks; observe software matches or an explicit live upstream failure rather than invented data.
- In App name mode submit `Tiimo`; observe title/developer candidates, confirm the intended listing, and see only that app. Return to candidates without a new API request. Verify that there is no silent first-result confirmation.
- Submit a phrase, edit the input without submitting, then change the country to India. Verify that the old submitted phrase, not the draft, is searched under `in`; the confirmed app is cleared and no US result is represented as Indian. Also exercise a rapid search/country change so an older response cannot overwrite the current view.
- Verify rating/count labels, metadata freshness, app-ID copy behavior, keyboard operation, and opening the original listing. Use a controlled upstream response through the same real API path to exercise missing metadata, empty results, rate limiting, and errors without depending on a live failure or deliberately exhausting Apple's service.
- Repeat a search and observe a cache hit with the same fetch time. Reload and observe that page state is cleared; a subsequent submission may still hit the running backend cache. Restart the backend and confirm that the same search requires a fresh fetch.
- Observe browser/backend network activity to confirm that only FastAPI calls Apple's Search API and that no review, Lookup API, AI, or background retry activity occurs. External icon requests and opening original listing links are expected and are not Search API calls.
- A live zero-result response or explicit upstream failure is an honest runtime outcome, but does not by itself prove the populated result/confirmation flows. Demonstrate those flows with a functioning live query and cover deterministic error/empty behavior through controlled upstream responses.

## Out of Scope

- Competitor classification, competitor sets, preselected top-ten apps, bulk selection, saved research, or research ownership.
- Review fetching, public RSS traversal, review storage, review-page navigation, rating filters for reviews, written-review counts, review analysis, or conversations over reviews.
- LangChain, LangGraph, LLM calls, inferred search intent, AI ranking, or exact-name confidence heuristics.
- Numeric ID/App Store URL input detection, Apple Lookup endpoints, bundle-ID lookup, or additional app-detail refresh operations.
- Google Play, Reddit, YouTube, macOS desktop software search, a separate iPad search mode, comprehensive catalog discovery, search-result pagination, and claims of complete coverage.
- Revenue/download estimates, rating-based result sorting, client-side exact-name boosts, and the optional extended description/version/pricing details panel.
- Accounts, authentication, teams, user-specific limits, databases, persistent caches, saved searches, saved URLs/workspaces, or cross-restart selection persistence.
- Public hosting, deployment pipelines, multiple backend workers, distributed locks/rate limits, Redis, production observability platforms, metrics dashboards, and agent orchestration.
- Typing debounce, automatic retries, background queues, stale-cache fallback, and automatic storefront fallback.
- Changes to the existing informational landing page or revival of historical implementation tickets.

## Further Notes

- This is a parent specification, not an implementation ticket. Apply `ready-for-agent` as requested by the specification workflow, but that label does not authorize implementation. The user must review this published spec before ticket drafting; ticket approval, assigned branches/worktrees, and explicit fresh-session implementation authorization remain separate gates.
- Scope and testing decisions were settled through the current conversation. The user approved the testing approach with “Approve testing approach.” Approval of this published specification, implementation tickets, or implementation itself has not yet been given.
- The original document, “Bibi — Apple App Store Discovery Module (MVP),” dated 2026-10-21, is source material rather than an overriding contract. This spec replaces its competitor/review actions, India default, typing debounce, and distributed infrastructure with the agreed narrower design. The original downloaded document remains unchanged.
- Historical [issue #7](https://github.com/sanketsingh27/bibi/issues/7) reports a completed review-research slice, and [issue #1](https://github.com/sanketsingh27/bibi/issues/1) describes a broader research workspace. Neither establishes that those modules exist in the current checkout or are dependencies of this search-only feature. Do not reopen, edit, or implicitly migrate those tickets as part of this spec.
- Current codebase terminology is App discovery, Keyword search, App-name search, App Store app, and Storefront. A discovered or confirmed app is not necessarily a competitor.
- Apple's [iTunes Search API documentation](https://performance-partners.apple.com/search-api) supplies the search parameters, approximate 20-calls/minute guidance subject to change, result-limit range, and promotional-content conditions. Bibi's 10-per-minute limit, 24-hour TTL, and 8-second deadline are chosen local policies, not Apple guarantees.
- Apple's [Availability of Apple Media Services](https://support.apple.com/en-us/118205) is the first-party reference for the supported-storefront catalog; App Store availability must be distinguished from availability of other Apple media services. Consult Apple's [App Store marketing resources](https://developer.apple.com/app-store/marketing/guidelines/) for approved badge usage. This specification is not legal advice or a claim of Apple endorsement.
- Live upstream checks on 2026-10-22 succeeded in the US storefront: `Tiimo` returned 40 records and `adhd planner` returned 45 with a requested limit of 50; the observed records were software with valid numeric IDs. These are recorded observations, not fixed acceptance counts. Catalog contents, ordering, titles, and availability can change.
- The live checks exercised Apple directly. No Next.js search application, FastAPI implementation, permanent tests, or browser end-to-end search was implemented or claimed as passing during specification planning.
