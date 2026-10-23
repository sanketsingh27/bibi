# Spec: Evidence-Linked Review Analysis and Local Retrieval

## Problem Statement

A list of written reviews does not directly explain what users praise, which complaints recur, what they request, or what opportunities those reports suggest. An AI summary can also fabricate evidence, hide sample gaps, omit long reviews, or substitute a handful of similar reviews for analysis of the complete sample.

The researcher needs evidence-linked review analysis with explicit scope, local embeddings, and retrieval that supports comparison without turning similarity into statistics. Saved reports must remain understandable when more reviews are fetched, the model changes, or a later operation fails.

## Solution

Add review-analysis on top of review-library and ai-runtime. Use the one selected OpenRouter text model through bounded LangChain/LangGraph steps to process every review in the chosen sample or star-filtered subset, validate structured findings against actual source IDs/quotes, and publish a report only after its scope and evidence are valid.

Create multilingual embeddings locally after explicit setup and persist their source associations in IndexedDB. Retrieve supporting evidence separately for each app/storefront/sample/topic. Retrieval supplements complete-sample analyses; it does not determine sample coverage, numerical star filters, incidence counts, or factual truth.

Automatically analyse an initial non-empty review sample when prerequisites are ready. Provide explicit Analyse filtered reviews and Update analysis actions. Fetching more reviews or changing Settings does not automatically replace a report or start another paid analysis.

## User Stories

1. As a researcher, I want the initial non-empty review sample analysed automatically when configuration is ready, so that selecting an app leads to findings without another research form.
2. As a researcher, I want missing key/model/local embedding setup shown as an action, so that an unmet prerequisite is not presented as finished analysis.
3. As a researcher, I want no report generated from an empty review sample, so that the model cannot invent customer feedback.
4. As a researcher, I want praise, recurring complaints, feature requests, and opportunities covered, so that the result supports product research.
5. As a researcher, I want every review in the chosen scope processed, so that a top-k similarity result does not replace complete-sample analysis.
6. As a researcher, I want long reviews split without silently losing their endings, so that relevant evidence remains included.
7. As a researcher, I want findings tied to actual review IDs, so that I can inspect supporting source text.
8. As a researcher, I want quotes checked against the referenced review, so that fabricated text is not accepted as evidence.
9. As a researcher, I want source app/storefront/sample scope enforced, so that another app's review cannot support this report.
10. As a researcher, I want theme counts calculated from unique valid source IDs, so that generated numbers do not become statistics.
11. As a researcher, I want reviewer claims described as reported feedback rather than proven product defects, so that the report does not overstate its evidence.
12. As a researcher, I want small or gapped samples clearly labelled, so that limited evidence is not presented as a market-wide trend.
13. As a researcher, I want complete-sample and filtered analysis stored separately, so that star-filtered findings cannot be confused with all saved reviews.
14. As a researcher, I want Analyse filtered reviews to be explicit, so that merely viewing a filter does not trigger another AI call.
15. As a researcher, I want the analysed count, filter, model, and generation time shown, so that report provenance remains visible.
16. As a researcher, I want fetching more reviews to preserve the existing report, so that downloading data alone does not create another analysis charge.
17. As a researcher, I want analysed-versus-saved coverage shown after expansion, so that an old report is not mistaken for analysis of the larger sample.
18. As a researcher, I want Update analysis to process the expanded scope explicitly, so that I control when the report is refreshed.
19. As a researcher, I want model changes to affect only new explicit work, so that saved reports retain their producing model and do not rerun silently.
20. As a researcher, I want a failure or cancellation to preserve the prior valid report, so that completed research is not lost.
21. As a researcher, I want partial extraction stages distinguished from a finished report, so that incomplete work is not presented as successful analysis.
22. As a researcher, I want explicit first-use local model setup, so that downloads and local processing requirements are visible.
23. As a researcher, I want embeddings created locally rather than through a remote service, so that semantic indexing does not silently share review text.
24. As a researcher, I want a pinned embedding model revision and saved index provenance, so that results are not mixed across incompatible vector spaces.
25. As a researcher, I want changed review text to invalidate stale derived indexes, so that retrieval uses the evidence actually being analysed.
26. As a researcher, I want original text and offsets retained through chunking, so that retrieved passages link to the complete saved review.
27. As a researcher, I want retrieved evidence scoped before ranking, so that an irrelevant app's highly similar text cannot enter this report.
28. As a researcher, I want distinct supporting review IDs rather than duplicated chunks counted as separate reviews, so that evidence is not inflated.
29. As a researcher, I want no retrieved evidence described as insufficient evidence, so that an absent result is not treated as proof the app lacks a feature.
30. As a researcher, I want the actual report-writing model used consistently across the operation, so that hidden model routing does not change the result midway.
31. As a researcher, I want provider and context failures reported honestly, so that the app does not silently analyse less data to produce a successful-looking report.
32. As a researcher, I want untrusted review/model content treated as data, so that it cannot issue tools, change Settings, or execute in the UI.
33. As a researcher, I want saved reports and indexes reopened without another paid request, so that persistence provides predictable reuse.
34. As a researcher, I want evidence links usable by keyboard and on narrow screens, so that findings remain inspectable without a desktop pointer.

## Implementation Decisions

### Capability, operations, and scope

- Stable module ID: review-analysis. Dependencies: review-library for source samples, persistence and transient operations; ai-runtime for key/model/configuration and the shared inference interface. No additional model provider, autonomous agent, server database, or durable graph checkpoint store is introduced.
- POST /api/v1/research/analyses accepts requestId, AppIdentity, the validated ReviewSample, stars as null/all or one integer from 1 to 5, and an optional compatible saved embedding index. It starts an analysis operation using the parent's HTTP 202/poll/cancel protocol. A zero selected-review scope returns an explicit no-data result without provider work, not invented analysis.
- The browser triggers one initial complete-sample analysis intent after initial collection succeeds or yields useful partial data, only when key/model/local embedding prerequisites are ready. Missing prerequisites show their setup action. Reopening an already saved report does not start that intent again. Normal catalog search/tab navigation does not analyse.
- Analyse filtered reviews creates an explicit narrower report for the current stored sample and numerical star scope. Update analysis explicitly targets the latest saved sample. Refresh reviews and analyse is a separate explicit parent intent. Fetching more reviews, filtering the display, reopening, or changing the selected model never silently starts a replacement report.
- Freeze the selected text model ID, sample fingerprint, star scope, and operation intent when work starts. Model changes later apply to future explicit work. The same process-local requestId/payload replays or joins; a changed payload conflicts. Lost process state does not authorize an automatic paid resubmission.
- Bound one analysis input to at most 500 distinct reviews with parent identity validation. Reject foreign review IDs/country, unsupported star scopes, malformed dates, non-finite/incompatible vectors, invalid fingerprints, and oversized payloads with a safe error rather than truncating the accepted sample. Support at least the actual public-feed review lengths used in the runtime smoke; enforce a 64 MiB request-body ceiling and a 20,000-character maximum text field per review, with explicit limit guidance for rejected inputs.

### Complete-sample extraction and validated reports

- Use a bounded LangGraph workflow with deterministic stages for input validation, source segmentation, per-batch extraction, aggregation, evidence/count validation, and final report creation. LangChain ChatOpenRouter is the only generative interface. Review content is untrusted data and cannot alter the graph's tools, key, model, fetch scope, or storage permissions.
- Process all review text in the chosen scope. Segment any long review using the selected model's input/token constraints and preserve source ID/offsets; do not drop the suffix through implicit token truncation. Fit every request within advertised context after system/schema/input/output accounting. Requests are sequential, have a 120-second deadline and at most 4096 output tokens, and have no hidden SDK retries or automatic different-model fallback.
- Per-batch output must identify the source review/chunk coverage that was processed, including reviews without an extracted theme. Aggregate only validated stages and verify that the successful complete report covers every selected review. If a batch fails, the operation may expose actual partial progress, but it must not mark an incomplete report as complete or lower analysedCount silently while claiming full scope.
- Structured themes identify praise, complaint, or feature request; each includes a label/description, supporting review IDs, and exact quote references where used. Opportunities link back to validated source themes/review IDs. Generated summaries have no authority to invent app features, download/revenue statistics, or unsupported prevalence claims.
- A successful report includes reportId, appId/country, sampleFingerprint, selected star scope, modelId, generatedAt, analysedCount, source-coverage warnings, summary, themes, opportunities, and evidence. Validate every evidence ID against the exact supplied source scope and every quoted string/offset against its original review text. A foreign ID or fabricated quote is an invalid result, not an invitation to manufacture a replacement source.
- Compute each reported theme count from unique validated supporting review IDs. A review may support multiple different themes, but repeated chunks/quotes for the same theme do not increase that theme's review count. Do not derive incidence from generated numbers or cosine scores. Label findings as what the sample's reviewers report, not established market-wide facts.
- Small samples remain analyzable if non-empty, with their actual count and limited-evidence warning; do not invent a threshold claiming representativeness. Source gaps/partial availability remain visible in the report. Invalid or failed output preserves the prior valid report; do not silently omit bad evidence and call the remainder a validated complete result.
- Do not automatically ask a model to repair invalid output, switch models, or rerun a paid batch. Recovery is explicit and must state any uncertain prior provider outcome. Stop additional dispatches on cancellation; an already sent call may still incur cost.

### Local embedding setup and index contract

- POST /api/v1/embeddings/setup starts an explicit embedding-setup operation using the shared coordinator. Display download/setup progress, failure, and cancellation where supported. Do not download model weights silently as a side effect of ordinary catalog browsing. Once setup is ready, a pending user-authorized initial research intent can continue; setup does not authorize arbitrary new paid work.
- Use intfloat/multilingual-e5-small at pinned revision 614241f622f53c4eeff9890bdc4f31cfecc418b3 through Sentence Transformers, under the model's MIT license. Run on CPU by default. Pin compatible dependency versions when implementing and retain the backend lockfile; optional acceleration needs real device verification, not an assumed speedup. Do not enable remote model code or replace failed local setup with a hosted embedding API.
- Use query and passage prefixes as the model card requires, including non-English input. Generate normalized finite 384-dimensional vectors. The model input ceiling is 512 tokens: tokenize passages into at most 480 tokens with 64-token overlap, including sufficient prefix/special-token headroom, and retain original source offsets. Segment instead of relying on silent truncation. Query text must also fit the model limit or be explicitly segmented/rejected, not silently altered.
- Weights/tokenizer are cached locally after explicit setup. A cached setup must support local embedding inference without network access; missing/corrupt weights or incompatible dependencies produce visible readiness errors. A model may support many languages, but no universal quality guarantee is inferred from its model card.
- EmbeddingIndex records identity, sampleFingerprint, model ID/revision, chunk IDs, source review IDs/offsets, and normalized vectors. Persist it in browser IndexedDB with its source sample association. Backend model cache may hold weights and bounded working arrays, not a persistent review database.
- Validate supplied saved indexes for exact scope/fingerprint/revision/dimension/finite values before use. Reuse matching chunks; rebuild changed source/revision data explicitly under the active operation. Never mix vectors generated by different model revisions or associate deleted review evidence with an available index.

### Retrieval and persistence behavior

- Use a bounded local cosine scan over the current validated app/storefront/sample/star scope, not a vector-database service. Filter source scope before similarity ranking. Retrieve at most five distinct supporting review IDs per app/topic; multiple chunks from one review must not be counted as distinct reviews.
- Retrieval provides relevant evidence for comparison topics and source inspection. It does not replace processing the complete sample, establish frequency, prove an individual claim, or prove that an app lacks a feature when no matching evidence was retrieved.
- Preserve exact original review text for evidence links, with selected chunks highlighted or navigable in the review display. Model-produced HTML/links are not trusted; local evidence targets include app/storefront, sampleFingerprint, and reviewId so an older report resolves its original source version after refresh. Historical cited samples remain retained until their dependent research is deleted. Optional external source links must be safe.
- Store complete-sample, filtered, and comparison reports separately. A newly fetched/changed sample marks older report/index associations stale rather than relabelling them as current. Display analysedCount versus saved review count and actual model/time/scope. Do not erase a prior valid report on failed save, provider failure, cancellation, or all-empty refresh.
- Save report/index provenance with the sample transaction boundary. On storage failure, show not-saved state and retain prior persisted valid data. Reopening a saved report/index makes no provider request. Deleting source research invalidates/removes dependent vectors/reports through the review-library lifecycle contract.
- Minimize external AI input to needed review text/stars and app context. Omit author/profile metadata, retain no-training endpoint restrictions, disclose external processing and different provider retention policies, and keep secrets out of prompts/output/errors. Local embeddings do not make OpenRouter generation offline.

## Testing Decisions

The approved primary automated seam is the real FastAPI HTTP API with pytest/HTTPX. Use the existing search-suite ASGITransport/controlled-transport pattern, preserve real validation/LangGraph orchestration, and isolate credential storage. Controlled OpenRouter responses make scope/output failures deterministic; they do not prove live AI quality. Deterministic embedding-boundary fixtures can prove filtering/citation integration, not real semantic similarity.

Permanent regression scenarios include:

- Entire selected sample processed across multiple context batches, including a long review with relevant text near its end; no top-k substitution or silent suffix loss.
- Full-sample versus one-star scope, no matches without provider dispatch, wrong app/storefront/sample IDs, duplicate source IDs, invalid quote text, and counts based on unique evidence IDs rather than model numbers.
- Missing key/model/setup, invalid model/context/output, interrupted batches, rate limits/cancellation, same-intent replay, and prior valid report preservation.
- Changed source text/model revision invalidates stale index/report reuse; non-finite/wrong-dimension vectors and cross-app evidence are rejected.
- Fetch-more and model changes do not automatically rerun existing reports; Update analysis explicitly produces a new coverage/provenance result.

Runtime proof must use the real local embedding model and actual UI:

1. Explicitly set up pinned weights and observe progress/readiness. Create local vectors for a small controlled corpus with distinct battery-drain and subscription-price topics. Query the battery topic and inspect the related source review ranked ahead of the unrelated topic, with another app/storefront excluded before ranking. This is a smoke observation, not a universal accuracy claim.
2. Disable network access after setup and confirm local embedding/retrieval works from cached weights. Confirm no OpenRouter embedding request exists and source offsets still resolve.
3. Through the actual page and an authorized OpenRouter key, analyse a real non-empty sample. Inspect praise/complaints/requests/opportunities, click citations, verify quote text/source IDs, and review whether claims are actually supported. Record model/time/count and source limitations.
4. Select a star filter without a provider call, then use Analyse filtered reviews. Confirm the narrower report's scope/count differs correctly and the complete-sample report remains identifiable.
5. Fetch more reviews, confirm no inference and an old-report coverage label, then explicitly Update analysis. Change model/reload/reopen and verify no automatic rerun. Exercise controlled bad output and storage/provider failure; verify the old valid report is retained.

Commands: backend virtual environment active, `python -m pytest`; API runtime `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`; frontend `npm run build`, then `npm run start -- --hostname 127.0.0.1 --port 3000`. Runtime page: http://127.0.0.1:3000. Use temporary controlled-upstream runners for deterministic failure demonstrations, never production fixture routes. Valid authorized key/credits and explicit model download are prerequisites for real inference/setup. No new frontend test framework is proposed.

## Out of Scope

- Jev, other decision-model sidecars, model routers, multiple per-task generative models, autonomous agent tools, automatic model switching, or hidden paid repair/retry calls.
- Remote embeddings, external vector databases, server research/graph-checkpoint databases, silent model downloads, or unverified acceleration/performance claims.
- Top-k-only analysis presented as full-sample coverage, counts from cosine scores/model prose, fabricated citations, market-wide incidence, or independently verified truth of reviewer claims.
- Automatic paid re-analysis on filter/tab/model/sample changes or reopening; replacing prior reports on failure; a research chat UI, exports, accounts, or cloud sync.
- A new frontend/helper test framework, source-text tests, invented AI benchmark results, or implementation authorization.

## Further Notes

Parent specification: [#20 — Local app details, review analysis, and competitor comparison](https://github.com/sanketsingh27/bibi/issues/20).

Published module specification: [#24](https://github.com/sanketsingh27/bibi/issues/24). Capability dependencies: [review-library #23](https://github.com/sanketsingh27/bibi/issues/23) and [ai-runtime #21](https://github.com/sanketsingh27/bibi/issues/21). These are specification dependencies, not implementation authorization.

Module ID: review-analysis. Dependencies: review-library and ai-runtime. Competitor-comparison consumes its report and scoped-retrieval contracts. The selected text model remains one model; the separately pinned local embedding model is an on-device index mechanism, not a second remote decision/report model.

The user confirmed the combined complete-sample/RAG design, explicit filtered/update actions, single OpenRouter model, capability map, and test seams. This specification remains pending user approval. Publication and ready-for-agent do not authorize implementation; accepted dependencies, credentials/runtime prerequisites, ticket approval, assigned branch/worktree and fresh-session authorization are still required.

Primary references: [LangChain models](https://docs.langchain.com/oss/python/langchain/models), [ChatOpenRouter](https://docs.langchain.com/oss/python/integrations/chat/openrouter/), [LangGraph](https://docs.langchain.com/oss/python/langgraph/overview), [retrieval](https://docs.langchain.com/oss/python/deepagents/retrieval), [embedding model card](https://huggingface.co/intfloat/multilingual-e5-small), and [pinned model metadata](https://huggingface.co/api/models/intfloat/multilingual-e5-small). Model revision/license/384-dimensional prefix-and-token requirements were verified from primary metadata/card; weights, compatibility, retrieval quality, and paid generation were not executed during planning.

Verify applicable source terms/permission for persistent review reuse and external AI processing before affected implementation tickets are ready. A user-provided authorized key/credits, a functioning OS credential store, and explicit local model setup are runtime prerequisites, not evidence of passing behavior today.
