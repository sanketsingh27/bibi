# Spec: App Details

## Problem Statement

Bibi's current discovery page identifies App Store listings and can confirm one result, but does not open a dedicated research page. The researcher cannot inspect an App Store–style product description, screenshots, or research tabs while preserving the submitted search and unfinished draft.

A name match does not establish app identity, and a listing's ratings are not written reviews. The new page must preserve those distinctions and remain usable when optional metadata or later research prerequisites are unavailable.

## Solution

Add the app-details capability to the existing local application. An explicit selection from either discovery mode opens a page identified by the numeric Apple app ID and selected storefront. Exact lookup supplies available listing details for an App Store–style header, followed by Analysis, Reviews, and Competitors tabs. Analysis is the initial tab; its contents integrate the dependent research capabilities rather than pretending analysis already exists.

Returning to search restores submitted results and draft edits. Opening or searching a catalog must not silently classify competitors or trigger review work before the explicit app selection defined by the parent research flow.

## User Stories

1. As a researcher, I want an explicit app-selection action in both search modes, so that I can open the intended listing's detail page.
2. As a researcher, I want lookup to use the selected Apple app ID rather than its name, so that similarly named listings are not substituted.
3. As a researcher, I want the selected storefront visible on the detail page, so that country-specific availability and listing ratings are understandable.
4. As a researcher, I want the app name, developer, icon, category, description, screenshots, and available version/price information, so that I can understand the product in one place.
5. As a researcher, I want optional missing metadata shown as unavailable, so that the page does not invent product facts.
6. As a researcher, I want a valid zero rating count distinguished from missing information, so that absence does not become a fabricated score.
7. As a researcher, I want listing rating counts labelled as ratings rather than written reviews, so that I do not infer review coverage from them.
8. As a researcher, I want the original App Store link available, so that I can inspect Apple's source listing.
9. As a researcher, I want unsafe listing or artwork URLs withheld, so that external data cannot create executable or misleading links.
10. As a researcher, I want descriptions and release notes rendered as plain text, so that listing content cannot execute in the page.
11. As a researcher, I want an artwork failure to leave the app identity readable, so that a failed image does not break inspection.
12. As a researcher, I want Analysis, Reviews, and Competitors tabs with Analysis selected initially, so that the research flow is predictable.
13. As a researcher, I want pending data, unavailable data, missing AI configuration, and failed operations distinguished, so that I do not mistake an unfinished task for a completed report.
14. As a researcher, I want to return to the same search results and draft, so that inspecting an app does not discard my discovery work.
15. As a researcher, I want switching apps or storefronts to invalidate stale view updates, so that an older response cannot replace the current app's details.
16. As a researcher, I want a missing listing reported honestly without another country or app being substituted, so that a failed lookup remains trustworthy.
17. As a researcher, I want a detail URL to retain app/storefront identity on reload, so that it can reopen saved research for the same scope.
18. As a researcher, I want saved detail information identified as saved when live lookup fails, so that local evidence is not presented as newly fetched metadata.
19. As a researcher, I want tab changes not to trigger fresh paid work, so that navigation does not create unexpected charges.
20. As a researcher, I want keyboard-operable selection, tabs, and back navigation, so that the page is accessible without a pointer.
21. As a researcher, I want screenshots and detail fields usable on narrow screens, so that the page does not depend on a desktop-sized viewport.
22. As a researcher, I want the existing discovery behavior retained without AI credentials, so that this feature does not make simple search dependent on OpenRouter.

## Implementation Decisions

### Identity, lookup, and response

- Stable module ID: app-details. Dependency: existing app discovery only. This is a capability in the existing Next.js/FastAPI app, not a service split or implementation ticket.
- The detail route uses an explicit positive safe-integer Apple app ID and supported lowercase storefront. A bookmark/reload can restore identity and consult saved research; it does not reconstruct an unrelated search session that was never persisted. Back-to-search within the current navigation session preserves submitted query/storefront/results, mode, confirmation context, and unsubmitted draft text.
- Add GET /api/v1/apps/{appId}?country=... using exact Apple ID lookup with software validation. Keep search/catalog routes usable and prevent dynamic app routes from shadowing them. Search submission/typing alone remains discovery-only; app selection is the parent flow's review-research trigger.
- Return a detail snapshot containing existing listing fields appId, country, name, developer, iconUrl, averageRating, ratingCount, category, and storeUrl, plus description, screenshot URLs, version, release information/notes, and formatted price where provided, with fetchedAt/cached metadata. Optional unavailable values are null or explicitly absent according to the response schema; never infer price, rating, version, or screenshot content.
- Confirm the returned record identifies the requested app and software entity. No result or a different app ID is an unavailable/mismatched lookup, never a name-based replacement. Unsupported identity/storefront input is validation failure before dispatch. Retain the existing safe field/URL normalization conventions.
- Extend the existing 24-hour transient listing-metadata cache pattern to exact app/storefront lookup, with identical-request sharing, actual original fetchedAt, and bounded expiry. This cache is not research persistence and must not introduce database storage. Existing search cache identity and response fields remain unchanged.
- Apple calls use the shared conservative budget of ten upstream dispatches per rolling 60 seconds, including failed attempts, and eight-second deadlines. Rate limits and upstream errors use the established safe error envelope; there is no automatic retry or country fallback.

### Page and dependent research content

- The header presents available app identity, description, screenshot gallery, listing ratings/category, price, and version/release information in an App Store–style hierarchy. Label the country and distinguish listing rating statistics from written-review sample statistics.
- Keep existing Apple artwork requirements: show approved artwork only with the proximate approved App Store badge linked to that listing, preserve original-listing attribution requirements, and do not download/cache artwork files as research data. Screenshot rendering must respect applicable asset terms rather than treating public URLs as blanket reuse permission.
- Treat all listing text as text and all URLs as untrusted. Only safe HTTPS listing/asset URLs may render; never expose javascript/data/executable schemes or misleading Apple-lookalike listing hosts. An image failure has a non-fabricated text fallback.
- Show Analysis, Reviews, and Competitors tabs with Analysis initially selected. Tab changes alone do not start fresh collection or paid analysis. Real progress/configuration/empty/error/report states come from the dependent capabilities, not fabricated success content or permanent placeholder panels.
- A selected app starts the parent initial-research flow only once for the relevant fresh intent. Reopening existing saved research shows saved data without automatic source or AI work. Metadata read and review/analysis operations are separate; lookup failure does not erase an existing valid saved sample/report.
- Tag requests/view updates with app/storefront and current navigation intent. Abort obsolete requests where possible and ignore late results whose identity no longer matches. Preserve backend source truth; do not suppress a legitimate error as an empty result.
- Back navigation restores current-session search context without an unnecessary Apple request when results remain available. Changing storefront deliberately clears incompatible confirmation/research selection and uses that storefront's own data. No global-to-local metric substitution is allowed.
- Maintain focus, labelled controls, accessible tab semantics, live progress/error announcements, readable missing-data states, and a single-column narrow-screen layout without horizontal page overflow. Existing search controls remain keyboard-operable.

## Testing Decisions

The approved automated seam is the real FastAPI HTTP boundary. Prior art is `backend/tests/test_search.py`, which exercises real routing/services using HTTPX ASGITransport while controlling Apple HTTP responses and time. Extend it for exact lookup and consumer-visible failure boundaries; do not create helper-name, source-text, incidental-wording, or fixture-echo tests.

Required deterministic API scenarios:

- Correct app/storefront identity and extended optional metadata; missing optional fields and valid null/zero distinctions.
- No returned software record, a mismatched app ID, malformed source envelope, unsafe URLs, and invalid input without country/name substitution.
- Static search/catalog routes remain usable after adding the dynamic route.
- Identical exact lookups share source work and cache their original fetch time; budget/timeout/upstream failures are visible using controlled time/transport.

Actual-browser runtime verification is required because API tests cannot prove navigation or visuals. With both real applications running:

1. Search by keyword, edit the draft without submitting, select a result, and verify the intended ID/storefront and actual detail header. Return and observe the same submitted results and unsubmitted draft without another search dispatch.
2. Repeat in app-name mode, including ambiguous names. Confirm the intended listing explicitly; do not auto-select the first match.
3. Navigate between apps/storefronts while a controlled response is held; release the older response and verify it cannot overwrite the newer page.
4. Exercise missing optional metadata, failed artwork, unavailable lookup, and saved data with live failure through a temporary controlled-upstream runner. Verify plain-text rendering and honest saved/error labels, not fake production fallbacks.
5. Inspect Analysis/Reviews/Competitors tabs, keyboard/focus behavior, and 320/768/1440-pixel surfaces. Verify tab changes alone make no paid call and the original App Store badge/link remains valid.

Commands: from backend with its virtual environment active, `python -m pytest`; run the API with `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`. From frontend, `npm run build`, then `npm run start -- --hostname 127.0.0.1 --port 3000`. Observe the actual application at http://127.0.0.1:3000. These are future implementation checks, not checks claimed to have run for this specification.

## Out of Scope

- Changing keyword/app-name search intent, adding search-as-you-type, accepting arbitrary upstream URLs, auto-selecting name matches, or claiming complete App Store search coverage.
- Implementing review collection, embeddings, model inference, or comparison inside this capability instead of their declared provider contracts.
- Fabricated tab content, hidden review/AI work on catalog search or tab changes, automatic paid reruns, and replacing a failed lookup with a different app/country.
- Native packaging, accounts, cloud storage, exports, a chat interface, unrelated visual redesign, a new frontend test framework, or an implementation branch/ticket.

## Further Notes

Parent specification: [#20 — Local app details, review analysis, and competitor comparison](https://github.com/sanketsingh27/bibi/issues/20).

Published module specification: [#22](https://github.com/sanketsingh27/bibi/issues/22). Specification dependencies: existing app discovery; no new module-spec blocker.

Module ID: app-details, stage 1, based on existing discovery. The other stage-1 capability is ai-runtime; this module does not require AI credentials to show listing details.

The user confirmed the design and selected **Approve map and tests**. This module specification remains pending user approval and is not implementation authorization. Publication with ready-for-agent does not bypass ticket approval, exact branch/worktree assignment, runtime prerequisites, or fresh-session implementation gates.

Source references: [Apple ID lookup examples](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html) and [Apple Search API](https://performance-partners.apple.com/search-api). Existing discovery specification [#14](https://github.com/sanketsingh27/bibi/issues/14) is prior art. Lookup fields were observed during planning, but availability/freshness and asset-use permission are not guaranteed by those observations.

No app code, tests, builds, or artwork downloads were run or changed for this specification. Actual end-to-end verification belongs to the future authorized implementation ticket.
