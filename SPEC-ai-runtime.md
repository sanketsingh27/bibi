# Spec: Local OpenRouter Settings and AI Runtime

## Problem Statement

Bibi's current local app has no AI credentials, model Settings, or inference boundary. The researcher wants to choose a model using one OpenRouter key without putting that secret into browser research storage or making configuration changes trigger unexpected charges.

Provider models differ in capabilities, context, eligibility, pricing, rate limits, and data policies. A successful public model-catalog request does not establish that a key can make inference requests or that a model can produce the required evidence-linked reports.

## Solution

Add the ai-runtime capability with local Settings for one OpenRouter API key and one compatible text model. Persist the key through the device's OS credential store and expose only safe readiness metadata to the browser. Discover compatible models, show published pricing, and capture the selected model for each explicit research operation.

Provide a narrow, bounded inference interface used by LangChain/LangGraph workflows. Validate requests/results, preserve privacy policy restrictions, prevent hidden retries/model switching, and distinguish configuration, credit, rate-limit, timeout, and model-output failures. Missing AI configuration must not break app browsing or public review collection.

## User Stories

1. As a researcher, I want to configure one OpenRouter key, so that I do not manage separate provider credentials for this feature.
2. As a researcher, I want the key saved securely on the device, so that it is not persisted in browser research data.
3. As a researcher, I want Settings to show whether a key is configured without returning it, so that I can check readiness without exposing the secret.
4. As a researcher, I want a locked or unavailable secure store reported clearly, so that the app does not silently use a plaintext fallback.
5. As a researcher, I want to change the selected model without re-entering or revealing the key, so that normal configuration changes remain simple.
6. As a researcher, I want to remove the key without deleting research, so that credential and research lifetimes remain independent.
7. As a researcher, I want a compatible text-model list from OpenRouter, so that unsupported decision/image/embedding models are not offered as report writers.
8. As a researcher, I want model names, context information, and published pricing visible, so that I can make an informed selection.
9. As a researcher, I want unavailable or incompatible models reported rather than silently substituted, so that I control the model used for paid work.
10. As a researcher, I want one model used for all generative tasks in a research operation, so that a report does not hide dynamic model changes.
11. As a researcher, I want each saved report to identify its producing model, so that later Settings changes do not rewrite its provenance.
12. As a researcher, I want saving or checking a key not to run a hidden paid prompt, so that configuration alone does not incur inference charges.
13. As a researcher, I want model changes not to rerun saved reports, so that I choose when new paid work starts.
14. As a researcher, I want app browsing and public review fetching available without a key, so that AI configuration is not a prerequisite for discovery.
15. As a researcher, I want missing credentials, insufficient credits, and rate limits distinguished, so that recovery instructions match the actual problem.
16. As a researcher, I want an unsupported context/model configuration rejected before a false completed report, so that the selected sample is not silently truncated.
17. As a researcher, I want external processing disclosed, so that local storage is not mistaken for local generative inference.
18. As a researcher, I want unnecessary reviewer-name/profile metadata omitted, so that AI payloads contain only needed evidence and context.
19. As a researcher, I want no-training provider policy restrictions retained, so that failure to find an endpoint does not silently weaken privacy.
20. As a researcher, I want model prices described as published rates rather than a guaranteed bill, so that costs are not understated.
21. As a researcher, I want spending-cap guidance without the app purchasing credits or altering budgets, so that account control stays with me.
22. As a local operator, I want credential errors, provider errors, and logs scrubbed of secrets, so that troubleshooting is safe.
23. As a local operator, I want hostile websites prevented from changing credentials or invoking paid local operations, so that loopback hosting is not mistaken for request authorization.
24. As a researcher, I want cancellation and timeout to preserve prior reports without an automatic replay, so that recovery does not silently duplicate charges.
25. As a researcher, I want invalid model output rejected as invalid output, so that a schema failure is not presented as a meaningful analysis.
26. As a researcher, I want no Jev or model router introduced implicitly, so that the single-model design remains understandable.

## Implementation Decisions

### Capability and Settings surface

- Stable module ID: ai-runtime. Dependency: the existing local app. Settings/catalog operations are usable before review-library introduces the transient research-operation coordinator. Later workflows consume this capability's settings/inference contract; this does not create another deployed service.
- Use the same fixed local backend proxy and error envelope as the parent specification. Add GET /api/v1/ai/settings, PUT /api/v1/ai/settings, DELETE /api/v1/ai/key, and GET /api/v1/ai/models. The browser never calls arbitrary provider endpoints or receives a stored secret.
- Safe Settings metadata includes hasKey, selectedModelId, and secure-store/readiness status. The write accepts a write-only OpenRouter apiKey and selectedModelId; model-only updates do not need a key round trip. Reject unsupported fields, unsafe inputs, and blank/malformed keys with safe validation messages. Do not echo key fragments in failure bodies.
- Store the key in an application-specific OS credential-store entry accessed through the backend. macOS Keychain is the current device target; other supported OS stores require actual platform verification. Do not enumerate unrelated entries, store plaintext files, use an insecure alternate keyring backend, or put secrets into IndexedDB, local/session storage, URLs, analytics, prompts, logs, or exception responses.
- Persist selectedModelId in a separate app-owned OS credential-store settings entry, not as an implicit value inside a review snapshot. It survives backend restart and browser-data clearing. Removing the API key may retain this non-secret preference; safe Settings still reports hasKey as false. Never enumerate unrelated credential entries to locate it.
- Do not claim a successful persistent save if secure-store writing fails or is locked. Preserve the prior working configuration on failed replacement. Deleting an absent app-owned key is an idempotent no-secret result; deleting the key leaves saved reviews/reports untouched. Clearing browser research storage does not delete the OS key.
- Configuration validation may use OpenRouter's authenticated key metadata endpoint without making an inference request. Do not create a hidden paid test prompt. Invalid/revoked keys, network failures, missing credits, and unsupported models remain distinguishable; do not treat catalog HTTP 200 as key validation.

### Model selection and inference boundary

- Use the official OpenRouter catalog through a fixed backend endpoint. Return model ID, display name, context length, supported parameters/capabilities, published prompt/completion rates, and metadata fetch time. Cache catalog metadata briefly rather than refetching on each render; stale/error state must remain visible and must not invent availability.
- Offer explicitly selected compatible text models only. Reject decision-only, embedding/image-only, dynamic router, and unsupported structured-output models as report writers. Validate required parameters/context before inference and surface a model-compatibility error if they cannot be met. A catalog row is not a guarantee that the user's account can access every endpoint.
- Use one selected OpenRouter text model for extraction, topic/relevance work, synthesis, and comparison in an operation. Capture the ID at start so a Settings change cannot swap it halfway through a report. Preserve actual model identity in each validated result; fail on an unexpected different-model substitution rather than relabelling it.
- LangChain's dedicated ChatOpenRouter integration is the shared generative interface. LangGraph performs bounded application steps defined by consuming capabilities; do not expose autonomous tools, arbitrary URL fetches, storage mutation tools, or a second decision-model path.
- Provider calls are sequential, with SDK retries disabled, a 120-second per-request deadline, and explicit output limits of at most 4096 tokens. Each request accounts for model context, system/schema overhead, and reserved output tokens. Split input according to the declared tokenizer/context contract rather than silently dropping source text. Workflows remain finite through parent limits of at most 500 reviews/app and four apps/comparison.
- A context/model constraint or invalid output is an honest failure with guidance, not permission to process fewer reviews while claiming complete-sample coverage. Do not add automatic prompt-repair requests, different-model fallbacks, unbounded retries, or paid background re-analysis.
- Parse/validate structured output before consumers receive a successful result. Consumers additionally validate app/storefront/sample evidence IDs, exact quotes, and counts. Typed JSON is not evidence that generated claims are true.
- Preserve the parent distinction between failures and uncertain outcomes. A timeout or cancelled network stream may still have incurred a provider charge. Do not automatically replay an uncertain paid operation, and do not promise durable exactly-once execution across backend restarts. Process-local requestId replay/join is owned by the shared operation coordinator when consumers invoke paid work.

### Privacy, costs, and local security

- Require provider endpoints whose declared data policy excludes training on submitted content. If no compatible endpoint remains, fail visibly rather than relaxing the restriction. Do not enable OpenRouter or third-party prompt logging/tracing opt-ins. Different upstream retention policies still apply and must be disclosed; this is not a promise of universal zero retention.
- Send required review text/stars and app context only. Omit reviewer-name and profile-link metadata. Free-text reviews can contain personal information; do not call the payload anonymous merely because author metadata is absent. Local embeddings stay outside OpenRouter's embedding API.
- Show published pricing as informational rates, with model/fetch provenance. Recommend a user-configured key spending cap. Do not purchase credits, mutate account budgets, or request management credentials. No per-run price guarantee is inferred from displayed rates.
- Keep both applications loopback-only and validate trusted Host/Origin/request context for credential mutations and paid operations. No permissive CORS or arbitrary upstream proxy destination. Reject hostile cross-origin operations even when a stored key exists; do not introduce an unrelated account system.
- Use safe machine-readable errors for configuration, secure-store unavailable/locked, authentication, insufficient credits, rate limiting, timeout, model compatibility, and invalid provider output. Honor provider retry/wait information by exposing it to the user; leave retry/resume explicit. Never return a raw upstream body that might contain the key or internal state.

## Testing Decisions

The approved automated seam is the real FastAPI API with pytest/HTTPX, extending the existing search-suite pattern. Keep routing, settings orchestration, and output handling real; control OpenRouter HTTP responses and time and use an isolated credential-store implementation rather than real user secrets. Do not replace the entire feature with a mock that returns the expected Settings/report result.

Permanent behavior scenarios include:

- First secure key save, safe Settings read, model-only update, replacement failure preserving prior configuration, secure-store lock/failure without plaintext fallback, and key deletion that preserves research.
- Valid/invalid catalog shapes, incompatible model selection, context failure, revoked key, credits failure, 429/deadline, invalid structured output, and unexpected model substitution with no false success or automatic fallback.
- No inference call when configuration is missing or when merely saving/testing Settings; no secret content in responses/errors/loggable messages.
- Host/Origin rejection for key mutation and paid work, with zero provider dispatch for a rejected request.
- One captured model per operation and no automatic rerun of prior reports after changing Settings, exercised with the consuming capabilities rather than source-text assertions.

Browser/runtime proof during implementation:

1. Start the real local backend and production frontend. Without a key, browse and fetch reviews; observe a Settings action instead of a fabricated report.
2. Save an authorized test OpenRouter key through Settings. Reload and observe safe configured status, not the secret. Use an isolated app-owned secure-store test entry for a round trip; do not inspect unrelated keychain data.
3. Choose a compatible text model and inspect its displayed prices. Verify Settings save/model changes issue no hidden inference. Run one explicit authorized analysis and inspect actual model identity and provider-bound minimized payloads.
4. Demonstrate invalid/revoked credentials, locked store, incompatible model, rate/credit errors, and hostile Origin using controlled boundary data. Verify no plaintext/browser-storage fallback and preserve the prior report.
5. Remove the test key through the app and confirm saved research remains. Confirm no secret in page data, URLs, console, network responses, or persisted research.

Commands: backend virtual environment active, `python -m pytest`; API runtime `python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1`; frontend `npm run build` then `npm run start -- --hostname 127.0.0.1 --port 3000`. The browser entry is http://127.0.0.1:3000. No new frontend test framework is proposed. Valid user-authorized key/credits are prerequisites for real inference; no paid inference is claimed during specification writing.

## Out of Scope

- Direct OpenAI/Anthropic/Google credentials, ChatGPT-plan OAuth, Jev, Jev Router, automatic model routing/switching, remote embeddings, hosted vector stores, or a separate agent platform.
- Account creation, credit purchases, budget administration, management-key access, generic OAuth/authentication features, unrelated keychain enumeration, and plaintext/browser secret fallback.
- Treating catalog access as live inference proof, treating typed output as factual truth, automatic paid retries, hidden prompt repair, or a guarantee that cancellation reverses billing.
- Automatic re-analysis on Settings/navigation/reopen/fetch-more changes, telemetry/tracing opt-ins, public hosting, cloud research storage, or a new frontend test suite.

## Further Notes

Parent specification: [#20 — Local app details, review analysis, and competitor comparison](https://github.com/sanketsingh27/bibi/issues/20).

Published module specification: [#21](https://github.com/sanketsingh27/bibi/issues/21). Specification dependencies: existing local application; no new module-spec blocker.

Module ID: ai-runtime. Dependency: existing local application. Stage 1 may proceed independently of app-details after future implementation authorization; the review-analysis capability depends on this contract and review-library.

The user approved the design, OpenRouter/single-model direction, capability map, and test seams. This specification itself remains pending user review. ready-for-agent publication is not implementation authorization; tickets, exact branches/worktrees, accepted dependencies, and fresh-session implementation remain separate gates.

Primary references: [LangChain ChatOpenRouter](https://docs.langchain.com/oss/python/integrations/chat/openrouter/), [OpenRouter model catalog](https://openrouter.ai/docs/guides/overview/models), [limits](https://openrouter.ai/docs/api_reference/limits), [data collection](https://openrouter.ai/docs/guides/privacy/data-collection), [provider policies](https://openrouter.ai/docs/guides/privacy/provider-logging), and [OS keyring documentation](https://keyring.readthedocs.io/en/latest/). The public catalog returned actual model metadata during planning. The device reported a default macOS keychain path, but secure-store integration/write/permissions and paid inference have not been exercised.

Open [#13](https://github.com/sanketsingh27/bibi/issues/13) is historical future-model-selection context, not an instruction to retain its obsolete fixed DeepSeek assumption. Do not close or rewrite that issue automatically.

Implementation prerequisites include an available secure OS store, compatible installed integration packages pinned in the backend lockfile, authorized OpenRouter credentials/credits and model access, and actual runtime verification. No application code or dependencies were changed for this specification.
