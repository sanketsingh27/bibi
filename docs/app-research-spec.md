# Spec: Local App Details, Review Analysis, and Competitor Comparison

## Problem Statement

Bibi currently helps a researcher discover Apple App Store apps and confirm an intended listing. Selecting an app does not yet provide a research page, written reviews, review analysis, or a comparison with other apps. Listing rating counts are not written-review counts, and search matches are not verified competitors.

The researcher wants to inspect an app in an App Store–style page, understand a bounded review sample with supporting evidence, find competitor suggestions, and compare selected apps. Research must remain on the local device, survive reopening, and avoid unexpected AI calls. Apple's public review feed can return useful data but has inconsistent availability and gaps between populated pages; the product must disclose those limits rather than fabricate coverage.

## Solution

Extend the existing local Next.js/FastAPI application with an App Store–style detail page and Analysis, Reviews, and Competitors tabs. Obtain app details by Apple app ID and storefront. Target up to 200 mixed-star written reviews on the initial review fetch; offer an explicit larger target of 500. Save the actual review sample locally and support exact local star-rating filters.

Automatically analyse the initial non-empty sample when the user has configured an OpenRouter key, selected a compatible text model, and completed explicit local embedding-model setup. Analyse the complete selected sample in bounded batches. Create local embeddings and use scoped retrieval to support evidence-linked review comparison, not to replace full-sample analysis or calculate counts. Fetching more reviews does not automatically replace an existing report: show its coverage and offer Update analysis.

Show five competitor suggestions, select none automatically, and allow manual app-name addition. The researcher can choose up to three competitors and explicitly request a side-by-side comparison with the original app. Keep data, evidence, sample counts, and unavailable states separate for each app/storefront.

Use one selected OpenRouter text model through LangChain and LangGraph. Keep review data, embeddings, and reports in browser IndexedDB; keep the key separately in the OS credential store accessed by the local backend. No Jev, dynamic model router, paid review source, cloud research database, or implementation is authorized by this specification's publication.

## User Stories

1. As a researcher, I want to select an app from either search mode, so that I can inspect the intended listing without repeating the search.
2. As a researcher, I want the detail page to use the app's numeric Apple ID and storefront, so that similarly named apps are not confused.
3. As a researcher, I want an App Store–style header with available identity, description, screenshots, listing ratings, category, price, and version, so that I can understand the product before reading analysis.
4. As a researcher, I want missing listing fields labelled unavailable rather than invented, so that incomplete metadata does not mislead me.
5. As a researcher, I want an original App Store link, so that I can inspect Apple's listing directly.
6. As a researcher, I want Analysis, Reviews, and Competitors tabs with Analysis initially active, so that I can move between findings, source evidence, and comparisons.
7. As a researcher, I want progress shown while research runs, so that a pending operation is not mistaken for an empty result.
8. As a researcher, I want returning to search to preserve submitted results and draft edits, so that inspecting an app does not discard my discovery work.
9. As a researcher, I want late responses for a previous app or storefront ignored by the current view, so that results remain correctly identified.
10. As a researcher, I want searching alone to remain discovery-only, so that typing or submitting a catalog query does not trigger review collection or paid analysis.
11. As a researcher, I want the first review fetch to target up to 200 written reviews, so that initial research has a bounded scope.
12. As a researcher, I want to explicitly request a target of 500 reviews, so that I can expand a useful sample without an unrequested background collection.
13. As a researcher, I want the actual fetched count shown beside the target, so that a shortfall is visible.
14. As a researcher, I want partial and unavailable review samples distinguished, so that a source failure is not presented as an app having no reviews.
15. As a researcher, I want missing intermediate pages disclosed, so that a non-contiguous sample is not labelled the latest complete set.
16. As a researcher, I want collection to continue past empty intermediate pages within its bound, so that later available reviews are not missed solely because an earlier page was empty.
17. As a researcher, I want duplicate source reviews counted once, so that repeated pages do not inflate sample size.
18. As a researcher, I want each sample to remain tied to its app and storefront, so that reviews from different scopes are not merged silently.
19. As a researcher, I want collection to be paced and bounded, so that requesting more reviews does not launch an unlimited parallel batch.
20. As a researcher, I want to cancel collection and retain completed partial data, so that I can stop waiting without losing useful results.
21. As a researcher, I want a rate-limited operation to preserve its work and show when I may resume, so that repeated automatic requests do not worsen the limit.
22. As a researcher, I want All stars and individual one-to-five-star filters over saved reviews, so that I can inspect feedback of a chosen rating.
23. As a researcher, I want star filtering to use recorded numerical ratings rather than AI judgment, so that a three-star filter is exact.
24. As a researcher, I want filters labelled as applying to the saved sample, so that I do not infer complete App Store coverage.
25. As a researcher, I want original review text, date, stars, and available version visible, so that I can judge the evidence behind a finding.
26. As a researcher, I want untrusted review text rendered as plain text, so that review content cannot execute in the page.
27. As a researcher, I want non-empty initial samples analysed automatically once prerequisites are ready, so that selecting an app leads to findings without another research form.
28. As a researcher, I want review analysis to cover praise, recurring complaints, feature requests, and improvement opportunities, so that it supports product decisions.
29. As a researcher, I want the entire selected sample processed, so that a similarity-selected subset does not stand in for full-sample analysis.
30. As a researcher, I want long reviews processed without silently dropping their endings, so that important evidence is not omitted.
31. As a researcher, I want findings linked to actual saved reviews, so that I can inspect their support.
32. As a researcher, I want exact supporting quotes associated with their source IDs, so that fabricated or cross-app evidence cannot appear as valid support.
33. As a researcher, I want reported theme counts based on unique supporting review IDs, so that generated prose or embedding scores do not create statistics.
34. As a researcher, I want small samples described as limited evidence, so that a few reviews are not presented as market-wide trends.
35. As a researcher, I want no analysis generated for an empty sample, so that Bibi does not invent findings.
36. As a researcher, I want Analyse filtered reviews to explicitly analyse a star-filtered subset, so that browsing a filter does not silently replace the complete-sample report.
37. As a researcher, I want filtered and complete-sample reports identified separately, so that their findings and counts cannot be confused.
38. As a researcher, I want a report to show its sample count, model, and generation time, so that I know what produced it.
39. As a researcher, I want fetching more reviews to leave the prior report intact, so that downloading evidence alone does not incur another analysis charge.
40. As a researcher, I want Update analysis to explicitly include the expanded sample, so that I control when paid work runs again.
41. As a researcher, I want stale report coverage clearly shown, so that a report covering 200 reviews is not presented as covering every subsequently saved review.
42. As a researcher, I want failures to preserve the prior valid report, so that a refresh or AI outage does not destroy completed research.
43. As a researcher, I want local embeddings created on my device, so that semantic indexing does not silently send review text to an embedding service.
44. As a researcher, I want explicit first-use embedding setup, so that a model download and its local resource requirements are visible.
45. As a researcher, I want saved indexes associated with their review sample and model revision, so that stale vectors are not mixed with changed evidence.
46. As a researcher, I want retrieved evidence filtered separately for each app and storefront, so that comparisons do not cite another app's reviews.
47. As a researcher, I want missing retrieved evidence described as insufficient evidence, so that it is not treated as proof a feature or complaint is absent.
48. As a researcher, I want automatic competitor suggestions based on the selected app's problem and category, so that I can find plausible alternatives.
49. As a researcher, I want same-problem suggestions preferred over broad category matches, so that the suggestions are useful rather than merely adjacent.
50. As a researcher, I want a reason shown for each suggestion, so that I can judge whether it is a useful competitor candidate.
51. As a researcher, I want suggestions labelled as suggestions rather than verified competitors, so that search relevance is not mistaken for confirmed competition.
52. As a researcher, I want five suggestions with none selected automatically, so that bulk review work starts only for apps I choose.
53. As a researcher, I want Add app to use app-name search and explicit listing selection, so that I can inspect a particular app without silently accepting the first name match.
54. As a researcher, I want duplicate and original-app entries excluded from the comparison set, so that each column represents a distinct app.
55. As a researcher, I want to select up to three competitors, so that comparison remains bounded and readable.
56. As a researcher, I want Analyse competitors to explicitly start the chosen comparison, so that viewing suggestions does not fetch and analyse every suggested app.
57. As a researcher, I want the original app and competitors compared side by side, so that praise, complaints, requests, and opportunities can be inspected together.
58. As a researcher, I want each app's actual sample size and shortfall visible, so that unequal evidence volumes are not hidden.
59. As a researcher, I want unavailable competitor data shown honestly without invented findings, so that a partially successful comparison remains trustworthy.
60. As a researcher, I want no overall winner declared from unequal samples, so that the product does not overstate what the evidence supports.
61. As a researcher, I want saved research listed by app and storefront, so that I can reopen a previous investigation.
62. As a researcher, I want reopening saved research to reuse it without automatic upstream or AI work, so that I control refreshes and charges.
63. As a researcher, I want explicit Refresh reviews and analyse and Delete research actions, so that updating and removing saved research are deliberate.
64. As a researcher, I want deletion to remove associated reviews, embeddings, and reports, so that deleted evidence does not survive in a derived index.
65. As a researcher, I want storage failures shown clearly, so that the interface never falsely claims research was saved.
66. As a researcher, I want clearing browser storage distinguished from deleting my saved key, so that local data lifetimes are understandable.
67. As a researcher, I want Settings to accept one OpenRouter key and one compatible text model, so that I do not manage separate provider credentials for this feature.
68. As a researcher, I want published model prices and capabilities visible before selection, so that the choice is understandable without an automatic model router.
69. As a researcher, I want the key persisted in the device's secure credential store, so that it is not left in browser storage or returned by settings responses.
70. As a researcher, I want model changes to apply to new explicit work rather than rerun saved reports, so that changing Settings does not trigger unexpected charges.
71. As a researcher, I want browsing and review fetching to work without a key, so that missing AI configuration does not block app discovery.
72. As a researcher, I want clear actions for missing keys, credits, supported models, or local model setup, so that configuration problems are not reported as successful analysis.
73. As a researcher, I want submitted review text and external processing disclosed, so that local storage is not mistaken for fully offline AI analysis.
74. As a researcher, I want reviewer-name and profile metadata omitted from AI payloads, so that unnecessary personal information is not shared.
75. As a local operator, I want key errors, provider errors, and logs to exclude secrets, so that troubleshooting does not disclose credentials.
76. As a local operator, I want untrusted websites prevented from triggering local credential mutations or paid operations, so that loopback hosting is not treated as sufficient request authorization.
77. As a researcher, I want retries of the same in-process user intent not to duplicate paid work, so that polling and accidental resubmission are safe within the stated process lifetime.
78. As a researcher, I want backend restarts and interrupted paid requests shown as uncertain rather than silently retried, so that recovery does not imply an exactly-once guarantee.
79. As a researcher, I want accessible loading, error, progress, filter, and comparison controls, so that keyboard use and narrow screens remain supported.
80. As a researcher, I want the full feature specified and verified before implementation approval, so that published planning issues are not mistaken for working app behavior.

## Implementation Decisions

### Capability boundaries and existing behavior

- The approved stable capabilities are app-details, ai-runtime, review-library, review-analysis, and competitor-comparison. They remain inside the existing local Next.js/React frontend and single-worker Python/FastAPI backend. App-details and ai-runtime are independent first-stage capabilities; review-library depends on app-details; review-analysis depends on review-library and ai-runtime; competitor-comparison depends on app-details and review-analysis.
- Retain the existing app-search/catalog API contract and its keyword/app-name intent, explicit confirmation, country validation, safe metadata, transient cache, and request sharing. Do not silently restore the older SQLite/DeepSeek implementation. The new app-detail action is an explicit cutover from merely showing the confirmed listing to opening its research page; both search modes can open a selected listing.
- Extend the fixed same-origin backend proxy to the owned API families required below. The destination remains the local FastAPI server; do not introduce a caller-controlled proxy URL or permissive CORS. Static search and storefront routes must not be shadowed by dynamic app-ID routes.
- Bind both applications to loopback and retain one backend process. Existing search metadata caching is not a research database. Browser persistence is authoritative for saved research; backend operation state is transient. No cloud or server research database is introduced to simplify client/backend data transfer.

### Shared identities, evidence, and persistence

- App identity is a positive, frontend-safe integer Apple app ID plus an existing supported lowercase storefront code. Explicitly validate both at API boundaries. Changing storefront changes scope; do not substitute a different country or mix data across storefronts.
- A normalized Written review contains reviewId as the source ID string, appId, country, nullable title, non-empty plain-text body, integer stars from 1 to 5, source update time, nullable app version, and fetch time. An original review link is optional and must be a safe Apple HTTPS link. Omit reviewer names and profile links from normalized research data. Listing average ratings and rating counts remain distinct from fetched written-review statistics.
- A Review sample contains its app identity, targetCount of 200 or 500, at most 500 distinct normalized reviews, attempted/empty/failed page numbers, last fetch time, targetReached, availability, and warnings. Deduplicate by app/storefront/reviewId. Keep the first usable record in source order within a fetch; an explicit refresh may replace an updated record without counting it twice.
- Compute a sampleFingerprint from canonical identity and sorted source IDs plus substantive review text, stars, update time, and version. Fetch timestamps alone must not change an otherwise identical sample fingerprint. Model outputs, indexes, and comparison inputs identify the exact fingerprints they used.
- Persist listing snapshots, review samples, local embedding chunks/vectors, complete-sample and filtered reports, comparison reports, and their provenance in IndexedDB. Save derived data and its sample association atomically enough that a failed write cannot leave a report claiming a nonexistent sample. Retain prior validated snapshots/reports until replacements are successfully stored, and retain historical sample versions while a saved report still cites them.
- Analysis scope is the sample fingerprint plus either all stars or one selected star value. A report identifies its app/storefront, scope, model ID, generation time, analysed count, summary, themes, opportunities, and source evidence. The displayed model is the actual selected model used, not a later Settings value.
- Evidence references must belong to the exact supplied app/storefront/sample/star scope. Evidence links resolve app/storefront plus sampleFingerprint and reviewId, not merely the latest text for that review ID; a refreshed edit must not change the evidence displayed by an older saved report. Supporting quotes must exist in that historical referenced text. Reject foreign or fabricated evidence as an invalid analysis result; do not quietly fabricate or silently repair a successful-looking report. Calculate theme counts from unique valid supporting review IDs. Counts describe classified support in the sample, not independently established market incidence or factual truth of reviewer allegations.
- Saved research deletion removes dependent local embeddings and reports, including comparison references that would otherwise present deleted evidence as available. Deleting research does not delete the separately stored key; deleting the key does not delete research. Clearing browser storage can remove research independently of the key. Report storage failures rather than using an undisclosed remote persistence fallback.

### App details and review-source behavior

- Exact detail lookup uses GET /api/v1/apps/{appId} with a country query. Return a listing snapshot with the existing listing fields, available description/screenshots/version/release information/price, and fetchedAt/cached metadata. Missing optional fields stay unavailable. A missing or unavailable listing is not replaced by a similarly named app.
- Use Apple's unauthenticated HTTPS customer-review JSON feed for the explicit app/storefront. Do not scrape App Store HTML, fall back to XML to satisfy the JSON requirement, introduce a paid review provider, infer undocumented upstream star filtering, or follow arbitrary source URLs.
- On initial app research, target 200 reviews. The larger target of 500 requires an explicit user action. Attempt at most ten distinct page numbers per requested fetch, continuing past empty intermediate pages, stopping when the target of unique records is met or a cancellation/rate-limit/error boundary is reached. Reuse validated same-scope saved records and attempted-page information for expansion/resume instead of counting or fetching duplicates unnecessarily. Explicit refresh can revisit source pages.
- Share the existing conservative Apple dispatch budget across search, lookup, and review requests: no more than ten upstream dispatches in a rolling 60 seconds, including failed attempts; use eight-second upstream request deadlines. Queue paced page dispatches within a bounded active operation rather than launching unlimited parallel work. Expose progress and cancellation during a wait. Honor Retry-After when supplied. Pause rate-limited work and preserve partial records; resumption/retry is user-triggered, with no automatic retry loop.
- A successful HTTP response without review entries is an unavailable page, not proof that the app has no reviews. Distinguish invalid envelopes, upstream errors, empty pages, rate-limited pauses, cancellation, and useful partial samples. Show actual records, gaps, request bounds, and fetch times. Never label a gapped sample as a complete latest-N collection.
- All stars and individual one-to-five-star display filters run over saved records using numerical fields. Neither embeddings nor AI decide a star rating. The filter label and counts identify the fetched sample, not all matching reviews in the App Store. Changing a filter does not trigger upstream requests or automatically replace a report.

### Shared operation API and state transitions

- Review-library introduces a small transient operation coordinator reused by later capabilities. Settings and model catalog access do not depend on it. Operation kinds are review-fetch, analysis, suggestions, comparison, and embedding-setup. States are queued, running, succeeded, partial, failed, and cancelled; progress identifies the actual stage and completed/total units where known.
- Starting asynchronous work returns HTTP 202 with operationId, kind, status, and scope. GET /api/v1/operations/{operationId} returns progress and the actual terminal result or a safe error. POST /api/v1/operations/{operationId}/cancel requests cooperative cancellation and prevents additional dispatches; an already sent provider request may still incur a charge. Do not call a cancelled/incomplete report finished.
- POST /api/v1/apps/{appId}/review-fetches accepts requestId, country, targetCount, and an optional validated existing Review sample for expansion/resume. POST /api/v1/research/analyses accepts requestId, identity, the Review sample, all-stars or a single-star scope, and a compatible saved embedding index if present. POST /api/v1/research/competitor-suggestions accepts requestId and the selected listing snapshot. POST /api/v1/research/comparisons accepts requestId, one storefront, and original-plus-one-to-three distinct competitor snapshots and any reusable valid reports/indexes. POST /api/v1/embeddings/setup starts an explicit local model setup operation.
- Browser-supplied saved data is untrusted and must be validated before use. Bound records to 500 per app and four apps per comparison, incoming JSON bodies to 64 MiB, each review text to 20,000 Unicode characters, each title to 1,000 characters, and each source ID to 1,024 characters. Validate finite vectors, dimensions, fingerprints, supported fields, and scope before work. Return a safe validation/size error instead of silently truncating the user's sample; normal public-feed text is segmented for processing rather than shortened. Chunk metadata references original review offsets rather than duplicating complete review bodies.
- A requestId represents one user intent and remains stable while polling or retrying that intent. In the running backend process, the same requestId and payload join/replay the same operation; a changed payload with that ID returns conflict. Retain completed operation descriptors for one hour and bound active work to avoid overlapping paid dispatches. These are process-local protections, not durable exactly-once execution across restarts.
- On a backend restart, lost operations are reported as interrupted/unknown and require explicit recovery; do not automatically resubmit paid work. Preserve the last completed browser-saved report. UI response identity checks prevent stale operation completions from overwriting a newer app, storefront, selection, or sample.
- Retain the existing structured error envelope with machine-readable code and safe message. Use validation/conflict/not-found/rate-limit/upstream/configuration errors consistently. Never return stored credentials, raw provider exception bodies, or internal stack traces.

### Shared error semantics

Synchronous validation/dispatch failures use the following stable codes and HTTP status. Failed asynchronous operations retain the same safe error code/message in their descriptor; retrieving an existing failed operation remains HTTP 200, not a false successful research result.

| HTTP status | Code | Meaning |
| --- | --- | --- |
| 422 | VALIDATION_ERROR | Invalid identity, count, star scope, field, or record |
| 413 | PAYLOAD_TOO_LARGE | The explicit request/body/text bounds are exceeded |
| 404 | APP_UNAVAILABLE | Exact listing unavailable in the requested storefront |
| 404 | OPERATION_NOT_FOUND | Unknown, expired, or lost transient operation |
| 409 | OPERATION_CONFLICT | Same requestId with a different payload or incompatible active intent |
| 409 | RESEARCH_STATE_CONFLICT | Saved sample/index/report associations are stale or inconsistent |
| 409 | AI_NOT_CONFIGURED | Required key or selected model absent |
| 409 | EMBEDDING_SETUP_REQUIRED | Local embedding model not ready |
| 401 | AI_AUTHENTICATION_FAILED | OpenRouter key rejected or revoked |
| 402 | AI_CREDITS_EXHAUSTED | Inference cannot proceed under the key's available credits/budget |
| 403 | LOCAL_REQUEST_FORBIDDEN | Untrusted local Host/Origin/request context |
| 422 | MODEL_INCOMPATIBLE | Selected model/context/capabilities cannot satisfy this operation |
| 429 | SEARCH_RATE_LIMITED | Shared local Apple dispatch budget reached |
| 429 | UPSTREAM_RATE_LIMITED | Apple rate limited the request |
| 429 | AI_RATE_LIMITED | OpenRouter/upstream model rate limited the request |
| 502 | UPSTREAM_ERROR | Invalid or failed Apple response, retaining existing discovery semantics |
| 502 | AI_PROVIDER_ERROR | Safe upstream inference failure |
| 502 | AI_INVALID_OUTPUT | Invalid structure, provenance, model identity, or evidence |
| 503 | CREDENTIAL_STORE_UNAVAILABLE | Secure store locked, absent, or failing |
| 503 | EMBEDDING_SETUP_FAILED | Explicit local setup/inference runtime unavailable |
| 504 | UPSTREAM_TIMEOUT | Apple request deadline exceeded |
| 504 | AI_TIMEOUT | Provider request deadline exceeded; billing outcome may be uncertain |

An empty review page/sample is represented by the source availability/result contract, not APP_UNAVAILABLE or a claim that the app has no reviews.

### OpenRouter key, model, privacy, and local request security

- GET /api/v1/ai/settings returns hasKey, selectedModelId, and safe readiness/store status only. PUT /api/v1/ai/settings accepts a write-only OpenRouter apiKey and selectedModelId; later model-only changes must not require exposing the saved key. DELETE /api/v1/ai/key removes the key without deleting research. GET /api/v1/ai/models returns compatible model IDs/names, context/capability metadata, published pricing, and fetch time.
- Persist the key through the OS credential store accessed by the local backend. Persist selectedModelId in a separate application-owned secure-store settings entry so it survives restart without becoming research data; deleting the key may retain that non-secret preference. Fail visibly if a secure store is unavailable/locked; do not write a plaintext file, browser store, research snapshot, or secret-return endpoint as a fallback. Never enumerate unrelated user entries. Saving/testing configuration must not make a hidden paid inference request.
- One explicitly selected compatible text model handles every generative task for an operation. Capture its ID at operation start. Filter out decision-only models, image/embedding models, and dynamic model routers. Confirm required text/structured-output/context capabilities; an unavailable/ineligible model fails with guidance rather than being silently substituted. Same-model upstream endpoint routing must retain the requested data policy.
- Show published pricing as informational rates, not a guaranteed final bill. Recommend an OpenRouter key spending cap, disclose that analysis costs depend on sample/model, and never purchase credits or change account budgets automatically. Use sequential provider requests, a 120-second per-request deadline, an explicit maximum output of 4096 tokens, context-fitting input batches, and no automatic SDK retries or different-model fallback. Finite loops derive only from bounded input data and the approved pipeline.
- Configure requests for providers whose declared policy excludes training on submitted data; do not silently relax this when no compatible endpoint exists. Do not enable remote prompt logging/tracing opt-ins. Provider retention policies differ. Review text and required app context pass through OpenRouter/upstream providers; local storage and local embeddings do not make generative analysis offline. Omitting author metadata does not guarantee review text contains no personal information.
- Loopback binding is necessary but not sufficient. Validate trusted Host/Origin/fetch context for local credential mutation and paid operations, keep the fixed same-origin proxy, and reject hostile cross-origin requests. Do not introduce an unrelated account/login system. Treat Apple data, model output, and IndexedDB data as untrusted; validate schemas and escape text. Review content is data, not permission to execute tools, fetch arbitrary URLs, change Settings, or mutate storage.

### Analysis, local embeddings, and comparison

- Use LangChain's dedicated OpenRouter chat integration and bounded LangGraph steps for extraction, aggregation, evidence validation, and comparison. This is not an autonomous agent loop. Initial analysis starts only for a non-empty collected sample after key/model/local embedding prerequisites are ready; otherwise show the required action. Browsing and collecting reviews remain available without AI configuration.
- Process every review in the selected scope. Use tokenizer/context-aware segmentation and batch aggregation so long reviews are not silently truncated. Keep source IDs and exact text offsets through processing. Reject an unsupported model/context or invalid structured output honestly; do not substitute a small top-k sample and claim complete-sample coverage.
- The local embedding default is intfloat/multilingual-e5-small at revision 614241f622f53c4eeff9890bdc4f31cfecc418b3, under its MIT model license. Run on CPU by default through Sentence Transformers; optional acceleration needs actual platform verification. Explicit setup downloads pinned weights to the local model cache, with progress/error state and no remote-embedding fallback or remote model-code execution. No weights were downloaded during planning.
- Use the model's query and passage prefixes, normalized 384-dimensional vectors, and a 512-token model limit. Segment passages into at most 480 model tokens with 64-token overlap while preserving review offsets; do not rely on silent model truncation. Query and passage vectors must use the same pinned revision. Changed source text or model revision invalidates affected derived indexes.
- Persist vectors/chunk metadata with the app/storefront/fingerprint/revision association in IndexedDB; the backend accepts validated saved snapshots for local processing after reopening. Use a bounded local cosine scan rather than a vector-database service. Retrieve at most five distinct supporting review IDs per app/topic from the correct sample and star scope. This evidence supplements full-sample analyses; similarity is not occurrence count, confidence in a factual claim, or proof that missing evidence means a feature is absent.
- Complete-sample, filtered, and comparison reports remain distinct. Larger review fetches and Settings changes do not rerun old reports. Keep prior reports with explicit analysed-versus-saved coverage until Update analysis or another explicit analysis action succeeds.
- Competitor suggestions derive problem terms from the selected listing metadata using the same selected text model and existing Apple text search. Prioritize same-problem candidates over broad category matches, explain relevance, exclude the original and duplicates, and show up to five honest suggestions. Fewer than five real candidates is not filled with invented apps. Manual app-name addition requires explicit selection of the intended listing.
- The comparison selection is original plus one to three distinct competitor apps in the same storefront. Suggestions and opening candidates do not automatically launch a bulk review collection. Analyse competitors explicitly obtains/reuses bounded data, performs any needed per-app analysis with the captured selected model, and generates the side-by-side report. Show unavailable or partial app scopes separately; never invent a missing column's findings or declare an overall winner from unequal samples.

## Testing Decisions

- The user approved one primary automated seam at the real FastAPI HTTP boundary using pytest and HTTPX. Prior art is the existing search API suite, which uses ASGITransport against real routes/services, MockTransport only at Apple's HTTP boundary, and controlled time. Extend that pattern to app details, transient operations, review collection, Settings/key behavior, analysis workflows, and comparison. Keep real application/LangGraph orchestration; isolate credential storage from real user secrets.
- Good permanent tests catch plausible consumer-visible errors, scope violations, count/limit boundaries, incorrect state transitions, secret exposure, and paid side-effect duplication. Do not assert helper names, file layout, exact incidental wording, fixture echoes, copied defaults, or source text. No separate helper or frontend unit suite is introduced merely to increase test counts.
- Critical controlled scenarios include empty page 2 followed by populated page 4, duplicate IDs across pages, source errors versus no records, 200/500/ten-page caps, cancellation during pacing, rate-limited partial data and explicit resume, wrong storefront/app evidence, invalid ratings/quotes/vectors, changed sample fingerprints, missing keys, zero-review no-inference behavior, model errors preserving prior reports, and same-intent replay versus changed-payload conflict.
- Deterministic embedding-boundary fixtures can prove evidence scoping and report integration, not semantic retrieval quality. During implementation, run the pinned local model on a small real-text topic example and observe scoped retrieval, then review live model findings against actual cited reviews. Neither source-code checks nor a mocked generative answer proves AI quality.
- Use actual browser runtime verification for detail navigation/back state, IndexedDB save/reload/reopen, star filtering, filtered analysis, fetch-more versus Update analysis, Settings readiness/key status, competitor selection/manual ambiguity/comparison, deletion, quota/storage failure, keyboard access, and narrow/wide surfaces. The HTTP suite cannot prove browser persistence or visual behavior. A temporary local controlled-upstream runner may demonstrate deterministic failures; never add production fixture routes or fabricated fallbacks.
- Backend automated command: from backend with its virtual environment active, run `python -m pytest`. Backend runtime command: `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`. From frontend run `npm run build`, then `npm run start -- --hostname 127.0.0.1 --port 3000`. Inspect the real local page and network effects at each capability's documented scenarios. Keep existing discovery regression tests and dependency audits relevant to changed installations.
- Runtime smoke must obtain a real public Apple sample or honestly record its limited/unavailable state; real local embedding setup/topic retrieval; an isolated secure-store round trip; and authorized OpenRouter analysis/comparison through the UI. A valid user-provided key/credits and explicit model download are prerequisites. Do not use the user's unrelated stored secrets. Published model catalog access is not inference proof, and no paid inference was run during specification preparation.
- Every future implementation ticket must list exact working directories, runnable behavioral commands, runtime scenarios, expected observations, and actual completion evidence. Passing tests or compilation alone does not complete the feature.

## Out of Scope

- Native mobile or desktop packaging, public hosting, accounts, cloud research storage, cross-device sync, exports, research chat, tracing/evaluation services, or an additional frontend test framework.
- Paid review-data vendors, App Store HTML scraping, XML review fallback, App Store Connect ownership credentials, authenticated private Apple endpoints, or a guarantee of complete/latest-contiguous/global review coverage.
- Star-filtered upstream fetching without a supported public contract; matching-star targets that imply all such App Store reviews; silent country substitution; fabricated apps, reviews, reports, or evidence.
- Separate direct OpenAI/Anthropic/Google credentials, ChatGPT-plan OAuth, Jev, decision-model sidecars, dynamic model routers, automatic model switching, autonomous tool agents, remote embeddings, hosted vector databases, or arbitrary provider/plugin tools.
- Automatic re-analysis after fetching more reviews, changing tabs/stars/model, or reopening saved research; unbounded retries, durable exactly-once promises after process loss, automatic credit purchases, and account-budget administration.
- Implementation tickets, code changes, dependency installation, commits/merges, issue closure, or implementation authorization as a consequence of publishing these specifications.

## Further Notes

Design confirmation: the user said **confirm design** after the consolidated design and five operating defaults. Testing/capability approval: after invoking `/to-spec`, the user selected **Approve map and tests**. Those approvals authorize specification synthesis and publication only. This parent specification and every module specification still require user review and approval before ticket drafting/publication and later fresh-session implementation authorization.

Published parent specification: [#20](https://github.com/sanketsingh27/bibi/issues/20). The following complete module specifications share the normative contracts above. Native parent/dependency relationships track the capability map; these are specifications, not implementation tickets or authorization to start work.

| Module | Published specification | Specification dependencies |
| --- | --- | --- |
| app-details | [#22](https://github.com/sanketsingh27/bibi/issues/22) | Existing app discovery |
| ai-runtime | [#21](https://github.com/sanketsingh27/bibi/issues/21) | Existing local app |
| review-library | [#23](https://github.com/sanketsingh27/bibi/issues/23) | [app-details #22](https://github.com/sanketsingh27/bibi/issues/22) |
| review-analysis | [#24](https://github.com/sanketsingh27/bibi/issues/24) | [review-library #23](https://github.com/sanketsingh27/bibi/issues/23), [ai-runtime #21](https://github.com/sanketsingh27/bibi/issues/21) |
| competitor-comparison | [#25](https://github.com/sanketsingh27/bibi/issues/25) | [app-details #22](https://github.com/sanketsingh27/bibi/issues/22), [review-analysis #24](https://github.com/sanketsingh27/bibi/issues/24) |

Existing discovery spec [#14](https://github.com/sanketsingh27/bibi/issues/14) remains the prior-art baseline. Closed [#7](https://github.com/sanketsingh27/bibi/issues/7) describes an older absent SQLite/Drizzle/Vitest implementation; open [#13](https://github.com/sanketsingh27/bibi/issues/13) describes future model selection retaining an older fixed DeepSeek model. This confirmed IndexedDB/OpenRouter feature supersedes those conflicting assumptions without restoring absent code or closing/editing legacy issues automatically.

Observed source evidence: [Apple Support US page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1130498044/sortby=mostrecent/json) returned 50 unique written reviews; [Notion US page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1232780281/sortby=mostrecent/json) and [page 4](https://itunes.apple.com/us/rss/customerreviews/page=4/id=1232780281/sortby=mostrecent/json) returned 100 unique reviews while pages 2–3 were empty; [Notion Canada](https://itunes.apple.com/ca/rss/customerreviews/id=1232780281/sortby=mostrecent/json) returned a distinct sample. These are observations, not service guarantees. Local star filtering was exercised on actual records. Public-feed rating probes did not produce usable filtered responses.

Primary technical references: [Apple lookup examples](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html), [Apple's separate authenticated review API](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps-_id_-customerreviews), [LangChain OpenRouter integration](https://docs.langchain.com/oss/python/integrations/chat/openrouter/), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [OpenRouter models](https://openrouter.ai/docs/guides/overview/models), [limits](https://openrouter.ai/docs/api_reference/limits), [provider data policies](https://openrouter.ai/docs/guides/privacy/provider-logging), [model card](https://huggingface.co/intfloat/multilingual-e5-small), and [OS credential-store library](https://keyring.readthedocs.io/en/latest/).

Implementation prerequisites must remain explicit: public-feed availability; applicable permission/terms for persistent review reuse and external AI processing; a working OS credential store; explicit model-weight download and compatible local runtime; a valid authorized OpenRouter key, compatible model and credits for live inference. Public access and this design approval are not legal permission or a passing runtime result. Unresolved rights/credentials/runtime prerequisites block affected implementation tickets until resolved; they do not authorize silent scope reduction or fake fallbacks.

Current evidence is planning/source research and specification validation only. No application changes, new dependencies, embedding-model download, secure-store write, paid inference, behavioral suite, frontend build, or implementation acceptance is claimed here.
