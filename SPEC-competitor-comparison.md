# Spec: Competitor Suggestions and Evidence-Linked Comparison

## Problem Statement

Finding an App Store app does not identify its real competitors, and sharing a category does not prove competition. The researcher currently cannot see useful alternative-app suggestions, add a particular app by name, or compare review evidence across selected apps.

Automatically fetching and analysing every search match would create unrequested source traffic and AI cost. Comparing unequal or unavailable samples without visible coverage could also produce misleading winners, unsupported feature claims, or evidence from the wrong app/storefront.

## Solution

Add competitor-comparison after app-details and review-analysis. Use the selected app's metadata and the same configured text model to form bounded Apple searches, show up to five honest competitor suggestions with relevance reasons, and prefer same-problem candidates over broad category matches. Select none automatically. Allow manual app-name search with explicit listing confirmation.

Let the researcher choose up to three competitors and explicitly invoke Analyse competitors. Obtain or reuse scoped review samples/reports/indexes and generate a side-by-side comparison with the original app across praise, complaints, feature requests, and opportunities. Each finding links to the correct app's written reviews and shows sample limits; unavailable scopes remain visible rather than being filled with invented findings.

## User Stories

1. As a researcher, I want automatic suggestions derived from the selected app's metadata, so that I can find plausible alternatives without inventing a search phrase myself.
2. As a researcher, I want same-problem apps preferred over broad category matches, so that relevance is more useful than category membership alone.
3. As a researcher, I want a reason shown for each suggestion, so that I can decide whether it belongs in my comparison.
4. As a researcher, I want suggestions labelled as suggestions rather than verified competitors, so that automated relevance is not overstated.
5. As a researcher, I want up to five real suggestions rather than fabricated filler, so that source limits remain honest.
6. As a researcher, I want the original app and duplicate app IDs excluded from suggestions, so that the comparison set contains distinct products.
7. As a researcher, I want no suggestions selected automatically, so that viewing the list does not authorize bulk research.
8. As a researcher, I want Add app to accept an app-name search, so that I can investigate a particular app absent from suggestions.
9. As a researcher, I want to confirm the intended manual-search listing by name/developer/ID, so that an ambiguous first result is not silently chosen.
10. As a researcher, I want manual additions to use the active storefront, so that comparable scopes are maintained.
11. As a researcher, I want opening a suggested app to use the same detail experience, so that I can inspect its identity and source before choosing it.
12. As a researcher, I want to choose up to three competitors, so that the workload and side-by-side display remain bounded.
13. As a researcher, I want duplicate, original-app, and cross-storefront selections rejected before work starts, so that invalid comparisons do not create source traffic or charges.
14. As a researcher, I want Analyse competitors to be explicit, so that the app does not collect and analyse every candidate automatically.
15. As a researcher, I want compatible saved samples/reports/indexes reused, so that comparison does not repeat completed work unnecessarily.
16. As a researcher, I want the source age and actual count of reused data visible, so that reuse is not mistaken for a fresh fetch.
17. As a researcher, I want missing data collected within the same bounded rules as the original app, so that competitor collection does not become an unlimited exception.
18. As a researcher, I want progress and cancellation across the comparison, so that I can control a multi-app operation.
19. As a researcher, I want the captured selected model used consistently, so that hidden routing does not change the analysis between apps.
20. As a researcher, I want praise, complaints, requests, and opportunities compared side by side, so that product differences can be inspected together.
21. As a researcher, I want each app's own sample size and coverage warnings shown, so that unequal evidence volumes are not hidden.
22. As a researcher, I want every comparative claim linked to the relevant app's reviews, so that I can verify its support.
23. As a researcher, I want retrieval scoped per app/storefront/sample before ranking, so that one app's evidence cannot leak into another column.
24. As a researcher, I want distinct reviews rather than duplicate chunks counted as support, so that repeated text does not inflate a claim.
25. As a researcher, I want no retrieved evidence labelled insufficient evidence, so that the report does not infer a feature is absent.
26. As a researcher, I want complete-sample analyses used alongside retrieved evidence, so that a few top matches do not replace broad review analysis.
27. As a researcher, I want unavailable competitor data shown explicitly, so that missing findings are not invented or silently omitted.
28. As a researcher, I want no overall winner declared from unequal samples, so that the product does not overstate what it knows.
29. As a researcher, I want changed selections, samples, or models to make report provenance/staleness clear, so that an old comparison is not relabelled as current.
30. As a researcher, I want a failed/cancelled update to preserve the last valid comparison, so that completed research is not lost.
31. As a researcher, I want deleting source research to remove or invalidate dependent comparison evidence, so that deleted reviews do not survive as apparently available sources.
32. As a researcher, I want saved comparison reports reopened without automatic AI work, so that persistence gives predictable reuse.
33. As a researcher, I want comparison controls and evidence usable by keyboard and on narrow screens, so that side-by-side research is accessible.

## Implementation Decisions

### Capability and suggestion contract

- Stable module ID: competitor-comparison. Dependencies: app-details and review-analysis, including their review-library/ai-runtime provider contracts. Reuse existing app search, exact listing identity, saved research, operation coordination, local embeddings, and the one selected OpenRouter text model. Do not introduce a second model, new service, or autonomous agent.
- POST /api/v1/research/competitor-suggestions accepts requestId and the selected app-detail snapshot and starts a suggestions operation. Validate identity/metadata and capture the selected model. If configuration is absent, show a Settings action; manual app-name discovery remains available without model inference.
- Derive concise problem terms from available name/description/category using the same selected text model, then issue bounded Apple text searches in the current storefront. Use at most one problem-oriented search and one category-oriented search per explicit suggestion intent, with existing supported query bounds and at most 50 returned matches per query. These calls share the parent's Apple request budget and deadlines. Missing descriptions/categories produce a visible limitation, not invented product metadata.
- Rank same-problem candidates ahead of broad category matches using available listing evidence and the captured model's bounded relevance judgment. Reasons identify whether the app is a same-problem candidate or broader category match; generated relevance is not verified competition. Keep source app IDs/developers visible and validate the model's selected IDs against actual returned matches.
- Exclude the original app and duplicate IDs, retain the current storefront, and show up to five actual suggestions. If Apple returns fewer useful candidates, show fewer with an honest state. Do not fabricate apps, recast arbitrary matches as exact substitutes, run unbounded extra queries, or silently use another country to fill the list.
- Show no automatic selection. Suggestion generation does not fetch all candidates' written reviews. Opening one candidate uses the common explicit app-detail selection flow; it is not permission to launch a bulk comparison or collect every suggested app.
- Add app uses the existing app-name search behavior in the selected storefront. The user explicitly confirms the intended listing, even for a single match, before adding it. Reject the original/duplicate IDs. No new URL/bundle-ID input modes or inferred first-result confirmation are added.

### Selection and explicit comparison operation

- The selected comparison contains the original app and one to three distinct competitor IDs, all in one supported storefront. Enforce the limit at both UI and API boundaries before source/model dispatch. Changing storefront clears incompatible selections rather than mixing scopes.
- POST /api/v1/research/comparisons accepts requestId, country, the original and selected competitor snapshots, their review samples, and any reusable reports/indexes. Validate all identities, sample fingerprints, evidence, vector revisions, star scopes and the parent's bounded payload rules before using browser-saved data. Return HTTP 202 and use the shared operation poll/cancel protocol.
- Analyse competitors is the explicit paid/bulk-work intent. Existing source data and reports are reusable only when identity/sample/scope/model associations match. Display cached/saved fetch and generation times; never call reused data fresh. If a model or sample changed, reuse valid raw evidence/index data where compatible but generate the necessary new report only inside the explicit comparison operation.
- Missing requested data uses the same mixed-star target of 200 initially, explicit larger target of 500, ten-page horizon, deduplication, shared Apple budget, timeout, page-gap and partial-state rules. A comparison is not an exception to source bounds or an authorization to fetch all storefronts.
- Process the original and chosen apps in a bounded workflow with sequential upstream inference, captured model, progress stages, and cancellation. Do not create an independent parallel fleet of model calls, hidden retries, or different-model fallback. The same requestId/payload shares/replays within the running process; changed payload conflicts and backend process loss does not imply exactly-once recovery.
- One app's source/configuration failure must not be replaced by invented findings. Retain its labelled unavailable/partial column and preserve successfully obtained data for other apps. A failed original scope makes the comparative result incomplete. If fewer than two app scopes have usable evidence, show the limitation and available individual research rather than ask a model to invent a cross-app conclusion.
- A cancelled or failed update retains the last validated saved comparison with its old scope/time/model. Completed partial data remains available as actual data, not a falsely completed full comparison. An already sent provider call may still incur cost; do not automatically re-submit an uncertain paid operation.

### Evidence-linked report and retrieval

- Present the original app and selected competitors side by side across praise, complaints, feature requests, and improvement opportunities. Show app/developer/storefront, actual analysed/saved counts, sample target/shortfall/gaps, source age, star scope, and model/time provenance per app.
- Base broad findings on each app's complete selected-sample analysis. Derive bounded comparison topics from those findings and use local retrieval only to select supporting evidence. Per topic, filter by app/storefront/sample/star scope before cosine ranking and retrieve at most five distinct supporting review IDs for that app. Multiple chunks of the same review are one source review, not additional votes.
- Validate every quote and citation against the correct app's actual sample. Reject foreign sample/model/index associations and fabricated quote text; do not silently move a citation to another app or drop bad references while calling the result validated. Evidence links include app/storefront, sample fingerprint, and review ID and open that saved source version in the common detail experience, not a later edited replacement.
- Distinguish observed review reports from factual product claims. A pricing complaint is evidence that a reviewer reported a pricing concern, not a verified current app price. Missing retrieved support is insufficient evidence, not proof a feature/problem is absent.
- Counts come from unique supporting IDs in the correct processed sample, not generated prose or vector scores. Display denominators and unequal coverage without ranking an overall winner or inferring global market prevalence. Do not normalize sparse samples into an unsupported certainty score.
- A comparison report identifies reportId, original and competitor IDs, country, each input fingerprint/star scope, each analysed count, selected model ID, generation time, validated findings/evidence, and partial/unavailable warnings. Preserve the producing model even if Settings changes later.
- Save validated comparisons in IndexedDB alongside their source associations. Changed selections/sample fingerprints/model settings make the stored report's scope/staleness visible, not automatically current. Reopening, navigating, filtering the review display, or changing Settings does not automatically re-run it.
- Deleting source research removes or invalidates affected stored comparisons so deleted evidence cannot still appear available. A storage failure is visible and cannot be reported as a persistent save. Do not add server research persistence to make browser snapshot transfer easier.

### User experience and privacy

- Keep the existing approved App Store-style app page and Analysis/Reviews/Competitors tabs. The Competitors tab exposes suggestions, manual addition, bounded selection, and the explicit Analyse competitors action; suggestions are not prechecked.
- Make candidate reasons, partial states, progress/cancel/resume, selection limits, and evidence navigation labelled and keyboard-operable. On narrow screens, preserve each column's app identity and sample metadata in a usable stacked or horizontally contained comparison region without overflowing the entire page.
- Use only the user's configured OpenRouter key and selected text model. Provider-bound input omits reviewer-name/profile metadata and retains no-training endpoint restrictions; disclose that required review text still leaves the device. Local query/passage embeddings remain local.
- Treat app metadata, review content, model output, and IndexedDB values as untrusted data. No model instruction can trigger arbitrary URLs, expand scope, mutate keys, or bypass user selection. Apply the parent's local Host/Origin protections and safe error envelope.

## Testing Decisions

The user approved one primary automated seam at the real FastAPI HTTP API using pytest/HTTPX, extending the existing search-suite pattern with controlled Apple/OpenRouter responses/time and isolated credentials. Keep suggestion/comparison orchestration and validation real; do not test helper naming, fixture echoes, incidental wording, or output length as proof of correctness.

Permanent behavior scenarios include:

- Actual search results only, original/duplicate exclusion, fewer than five candidates without filler, missing metadata, wrong model-selected IDs, and explicit same-problem/category reason provenance.
- Ambiguous manual app-name results require confirmation; original, duplicate, cross-storefront, zero-competitor and more-than-three selections fail before source/model work.
- Suggestion generation and opening a candidate do not launch automatic bulk review fetches. Analyse competitors explicitly obtains/reuses only the chosen scopes.
- Saved data/model/fingerprint reuse versus stale data requiring explicit new work; a model change during execution does not swap the captured model.
- Empty/missing/partial app samples, original unavailable, insufficient comparable scopes, cancellation/rate limits, process-local replay/conflict, and prior comparison preservation.
- Cross-app/storefront evidence or stale vectors rejected; exact quotes/count denominators remain correct; no invented missing findings or overall winner from unequal samples.

Runtime verification through the actual UI:

1. Select a real app and inspect automatic suggestions. Verify actual IDs/reasons, no preselection, and no written-review requests for all suggestions merely because the list rendered.
2. Use Add app with an ambiguous name; explicitly confirm the intended listing. Attempt duplicate/original/fourth selections and observe the limit before dispatch.
3. Select up to three competitors, press Analyse competitors, and observe progress, actual per-app counts, model identity, partial states, and a side-by-side report. Click evidence in every available app column and verify text/IDs/app/storefront match. Use an authorized key and review actual generated support, not just a mock answer.
4. Through a temporary controlled-upstream runner, make one selected app unavailable and hold/cancel another stage. Observe labelled limitations, useful saved partial data, and preservation of the prior valid comparison without fabricated columns.
5. Fetch more evidence or change the model/selection after a completed comparison. Confirm the old report is not relabelled or automatically rerun. Reopen saved research, delete a source scope, and verify dependent comparison evidence no longer appears available. Check keyboard use and narrow/wide layouts.

Commands: backend virtual environment active, `python -m pytest`; API runtime `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`; frontend `npm run build`, then `npm run start -- --hostname 127.0.0.1 --port 3000`. Use http://127.0.0.1:3000 and inspect actual network, UI, and saved research. No new frontend test framework or production fixture endpoints are proposed. Real comparison requires authorized OpenRouter credentials/credits, local model setup, and source availability; no live comparison has been run for this specification.

## Out of Scope

- Verified/exhaustive competitor classification, market-share claims, automatic candidate selection, unlimited competitors, cross-storefront comparison, or an overall winner from unequal review samples.
- Fetching/analysing all suggestions automatically, automatic comparison reruns, hidden model switching, Jev/routing sidecars, autonomous tools, or unbounded source/model retries.
- New review-data vendors, HTML scraping, source-country substitution, guaranteed complete/latest samples, fake missing findings, or citation reassignment across apps.
- Accounts, server research databases, cloud sync, exports, research chat, an extra frontend test framework, and implementation authorization from publication.

## Further Notes

Parent specification: [#20 — Local app details, review analysis, and competitor comparison](https://github.com/sanketsingh27/bibi/issues/20).

Published module specification: [#25](https://github.com/sanketsingh27/bibi/issues/25). Capability dependencies: [app-details #22](https://github.com/sanketsingh27/bibi/issues/22) and [review-analysis #24](https://github.com/sanketsingh27/bibi/issues/24). These are specification dependencies, not implementation authorization.

Module ID: competitor-comparison. Dependencies: app-details and review-analysis, including the latter's review-library and ai-runtime contracts. This is the final capability in the approved dependency map; every selected comparison still relies on the same source and evidence limits as individual research.

The user approved five suggestions/no preselection/up to three competitors/manual addition, same-problem or category relevance, evidence-linked side-by-side comparison, one selected OpenRouter text model, capability boundaries, and test seams. This module specification remains pending user review. A ready-for-agent label is not approval to implement; tickets, branches/worktrees, accepted dependencies and fresh-session authorization remain later gates.

Apple's [Search API](https://performance-partners.apple.com/search-api) documents text matches and ID lookup, not a verified competitor endpoint. [OpenRouter](https://openrouter.ai/docs/guides/overview/models) and [LangChain](https://docs.langchain.com/oss/python/integrations/chat/openrouter/) provide the selected model interface; they do not make relevance judgments or review claims automatically correct. Evidence quality needs actual runtime review.

Source reuse/AI-processing permission, public-feed availability, explicit local model setup, secure-store availability, and an authorized OpenRouter key/model/credits are implementation prerequisites. No paid inference, comparison, embedding download, application change, build, or behavioral test run is claimed by this specification.
