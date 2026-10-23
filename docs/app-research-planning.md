# App details, review analysis, and competitor research

Status: the user confirmed the design with “confirm design” and then selected **Approve map and tests**. The parent specification and five module specifications are published as GitHub issues #20–#25. User approval of the published specifications is pending. Implementation tickets and implementation still require their later approval gates.

## Settled with the user

- Q23 is approved: selecting an app opens an App Store-style detail page with available icon, name, developer, listing rating, category, description, screenshots, and version. Below the app details, show **Analysis**, **Reviews**, and **Competitors** tabs. Open Analysis by default, show progress, and preserve search results when returning.
- Q22/Q25/Q27 are approved together: the initial review fetch targets up to 200 mixed-star written reviews per app and storefront. The user can explicitly request a larger target of up to 500, fetched through bounded, paced groups of page requests with progress and cancellation. Show actual counts and partial/unavailable status; neither target guarantees complete or contiguous latest-review coverage. The confirmed operating defaults cap each requested fetch at ten distinct page numbers. Catalog searching alone must not fetch reviews; this is the initial review fetch after selecting an app. Reopening saved research retains Q20's no-automatic-refresh behavior.
- Analysis covers what users like, recurring complaints, requested features, and opportunities for improvement. Findings link to supporting reviews; counts concern the fetched sample only. The user accepted this recommendation explicitly.
- Find competitor suggestions automatically using the selected app's metadata. The user considers apps addressing the same problem or sharing its category eligible suggestions. Matching/ranking follows the confirmed defaults below.
- Q19 is approved: show five competitor suggestions, select none automatically, and let the user choose up to three competitors for comparison against the original app. Keep a **+ Add app** control for manual app-name search. An explicit **Analyse competitors** action fetches reviews and compares the chosen apps.
- Q24 is approved: compare the original app and selected competitors side by side across praise, complaints, feature requests, and improvement opportunities. Link findings to written reviews, show each sample's size, and do not declare an overall winner from unequal samples.
- Use LangChain and LangGraph for the analysis/comparison workflow. Q26 selects an OpenRouter API key instead of separately configuring direct OpenAI, Anthropic, and Google credentials. Q28 selects one model in Settings for all AI tasks for now; save the producing model with each report, and do not automatically rerun reports when the model selection changes. The earlier direct-provider/ChatGPT-plan discussion is superseded for this feature. After reviewing the Jev findings, the user replied “ok”; retain one selected text model, with no Jev model or Jev Router integration in this feature.
- Save research in IndexedDB, as explicitly requested. The data is browser-local rather than a server database or cross-device account.
- Settings configures the user's OpenRouter key and selected model. The key must be securely persisted on the device, separate from IndexedDB research data. Use the local backend's OS credential store rather than browser-readable persistent secret storage; no secret value should be returned to the browser after saving. No OpenRouter integration or secure-store operation has been implemented.
- Bibi will remain a local tool, as explicitly confirmed by the user. External review sources and AI providers still require network access; local operation does not imply offline operation or establish open-source licensing.
- The user approved the combined approach with “use the combined approach”: analyse the complete fetched review sample and use local embeddings/RAG to retrieve evidence for review comparison. This approves the design direction, not implementation or a review-data vendor.
- The user accepted Q20: reopening research shows the saved result without another AI request; **Refresh reviews and analyse** explicitly updates it; **Delete research** removes that app's saved written reviews, embeddings, and analysis from the device. Saved-research navigation and storage-failure behavior follow the confirmed defaults below.
- Q29 is approved: fetching a larger review sample does not automatically rerun analysis. Keep the existing report, clearly show how many of the saved reviews it covers, and provide an explicit **Update analysis** action.
- The user selected Apple's open JSON endpoint for App Store written reviews, not a paid provider, and explicitly accepted the observed source limits. Live validation demonstrates populated public JSON responses for Apple Support US and Notion US/CA; inconsistent coverage and pagination require partial/unavailable outcomes, not a paid fallback.
- Support **All stars** and the App Store's 1–5-star ratings for display and filtered analysis. The user requested verification of upstream star-filter support before relying on it, and approved filtering locally stored written reviews if it is unavailable. No supported public-feed star parameter was established by the check below, so use exact local rating-field filtering over the fetched sample; embeddings remain for semantic retrieval, not numerical rating selection. The **Analyse filtered reviews** action is in scope; preserve the distinction between complete-sample and filtered analyses.

## Confirmed operating defaults

The user approved these five defaults with “confirm design”. They do not add autonomous agents, another inference model, a cloud database, or a paid review source.

1. **Bounded fetching:** scan at most ten distinct public-feed page numbers per app/storefront during a requested fetch, stopping earlier when its 200/500 unique-review target is met or the user cancels. Continue past empty intermediate pages within the bound. Use paced page requests under the existing conservative Apple request-budget pattern, not an unlimited parallel batch. Honor a rate-limit wait and preserve partial data; show a user-triggered resume/retry rather than an automatic retry loop. The public feed has no verified throughput guarantee.
2. **Candidate relevance:** use the selected app's name, description, and category to form Apple searches; the same selected text model can derive problem terms. Prioritize same-problem candidates over broad category matches, exclude the original app and duplicates, and show why each is suggested. Keep the label **Competitor suggestions**, not verified competitors. Manual app-name addition requires selecting the intended listing, not accepting the first name match automatically.
3. **Analysis boundaries:** with no key/model configured, browsing and review fetching remain available; show a Settings action instead of inventing analysis. With zero fetched reviews, do not call the model. For a small non-empty sample, state the count and limited evidence rather than claiming market-wide trends. Keep prior saved results when a refresh or AI call fails, labelled with their original sample/time/model. Star filters affect review display; **Analyse filtered reviews** explicitly creates the narrower report.
4. **Model and privacy:** Settings chooses one compatible text model from OpenRouter's catalog and shows its published pricing. No automatic switch to a different model or Jev router, and no second decision-model call. Review analysis shares required review text/stars and app context with OpenRouter/upstream providers, not reviewer-name/profile-link metadata; free-text reviews can still contain personal information. Prefer endpoints whose policy excludes training on submitted data and disclose that provider retention policies differ. Keep embeddings local; any embedding-model setup/download must be explicit, not a hidden remote-embedding fallback. Recommend an OpenRouter key spending cap; do not create account budgets or purchase credits automatically.
5. **Local research lifecycle:** provide a Saved research list grouped by app/storefront. Keep review records, local embeddings, and reports on this device through IndexedDB; the backend accesses the separate OS credential store. Clearing browser storage removes research, not the separately stored key. Save/storage failures must be visible and never claim persistence succeeded. Reopening saved research, changing tabs/stars/model, or fetching more reviews must not automatically rerun old reports; use the already approved refresh/update actions. No accounts, cross-device sync, exports, or chat interface are added.

Technical request/token limits, local embedding-model choice, API contracts, and exact verification commands belong in the specification. They must preserve these agreed boundaries and must not be used to narrow the requested feature. No qualifying hard-to-reverse, surprising architecture tradeoff requiring a separate ADR has been identified at this stage.

## Approved capability map

The feature contains independently testable capabilities. These are responsibility boundaries inside the existing Next.js/FastAPI application, not new deployed services or implementation tickets. Stable module IDs will connect the specifications and later ticket contracts.

| Module ID | Responsibility | Depends on | Build stage |
| --- | --- | --- | --- |
| `app-details` | Exact listing lookup, App Store-style detail page, and return-to-search state | Existing app discovery | 1 |
| `ai-runtime` | OpenRouter key/settings, OS credential storage, compatible model selection, and the shared inference boundary | Existing local app | 1 |
| `review-library` | Public JSON review collection, bounded progress/cancellation, IndexedDB research, star filtering, refresh, and deletion | `app-details` | 2 |
| `review-analysis` | Complete-sample and filtered analysis, local embeddings/RAG, evidence links, and explicit updates | `review-library`, `ai-runtime` | 3 |
| `competitor-comparison` | Metadata-based suggestions, manual app selection, and evidence-linked side-by-side comparison | `app-details`, `review-analysis` | 4 |

Stages define dependency order; stage-1 capabilities are independent. Each capability needs its own scoped specification contract before implementation tickets. The project still requires parent-spec approval, ticket approval/publication, and fresh-session implementation authorization later.

## Approved testing approach

Prior art inspected: `backend/tests/test_search.py` exercises real FastAPI routing/services using `httpx.ASGITransport`, controls Apple responses with `httpx.MockTransport`, and supplies controlled time through `create_app`. `frontend/package.json` configures build/dev/start but no frontend behavioral test runner.

- **One primary automated seam:** extend the real FastAPI HTTP boundary with pytest/HTTPX, not separate helper suites. Exercise app details, review collection, shared AI/credential behavior, analysis workflows, and comparison through consumer-visible API operations. Control external Apple/OpenRouter responses and time; isolate credential tests from real user secrets. Keep LangGraph/application orchestration real. Deterministic embedding-boundary input is suitable for scope/citation tests, but cannot establish semantic retrieval quality.
- **Permanent regression scenarios:** empty intermediate review pages followed by populated pages; deduplication and 200/500/ten-page bounds; partial collection on rate limit/cancellation; app/storefront isolation; invalid or mismatched evidence IDs; zero-review/no-key behavior without paid calls; failure preserving prior reports; no secret exposure through responses/errors. Assert behavior, boundaries, and state transitions, not helper layout or incidental wording.
- **Actual-browser runtime verification:** exercise the real Next.js/FastAPI UI for detail navigation and retained search state; IndexedDB reload/reopen; star filtering and filtered analysis; fetch-more versus explicit Update analysis; competitor selection/manual addition/comparison; settings/key status; deletion and storage failure; keyboard access and narrow/wide layouts. The API suite cannot prove browser storage or UI behavior. Use a temporary controlled-upstream runner for deterministic failure states, not fixture routes or fake production fallbacks. No new frontend test framework is proposed.
- **Real dependency smoke:** verify Apple populated/partial outcomes, local embedding creation and topic retrieval, and one authorized OpenRouter analysis/comparison through the UI. A valid user-provided OpenRouter key/credits and any explicit local model download are prerequisites; catalog access alone is not inference proof. Inspect provider-bound payloads for the approved minimization and verify secure credential round trips with an isolated test entry, not existing user secrets. Live AI output needs evidence review, not an asserted guarantee of model truth.
- **Commands and evidence:** the existing backend command is `python -m pytest` from `backend/` with its virtual environment active. The production frontend command is `npm run build` from `frontend/`. Runtime commands and exact observable steps will be specified per capability/ticket. No tests, builds, credential writes, model downloads, or paid inference were run for this proposal.

Existing issue context checked: closed [#7](https://github.com/sanketsingh27/bibi/issues/7) reports an older `web/` implementation with SQLite/Drizzle and Vitest; that is not the current Next.js/FastAPI checkout or its reusable test seam. Open [#13](https://github.com/sanketsingh27/bibi/issues/13) describes future model selection while retaining fixed DeepSeek for an older V1. The confirmed IndexedDB/OpenRouter design supersedes those conflicting assumptions for this new feature. Reference the historical issues in the specification rather than restoring absent code, inheriting obsolete scope, or closing/editing those issues without authorization.

The user selected **Approve map and tests** after invoking `/to-spec`. Specification synthesis and GitHub publication may proceed using these boundaries and testing seams. This approval is not specification approval or implementation authorization.

## Source feasibility evidence

### App details and discovery

[Apple's Search API documentation](https://performance-partners.apple.com/search-api) describes text search, storefront selection, result limits, and ID lookup. [Apple's archived Lookup examples](https://developer.apple.com/library/archive/documentation/AudioVideo/Conceptual/iTuneSearchAPI/LookupExamples.html) explicitly demonstrate looking up an app by Apple ID. ID lookup is appropriate for the selected listing; name search is not exact identity verification.

No arbitrary-app competitor or similar-app endpoint was found in the Apple Search/Lookup documentation reviewed. Search matches and shared categories do not establish competition. Automatic suggestions must not be represented as verified competitors solely because Apple returned them. This is a finding about the reviewed documentation, not proof that no related Apple feature exists elsewhere.

### Written reviews

[Apple's customer-review endpoint](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps-_id_-customerreviews) supports a maximum page size of 200. It is an App Store Connect API for apps accessible to the developer's account, not an unauthenticated arbitrary-competitor review API. See [App Store Connect API access](https://developer.apple.com/help/app-store-connect/get-started/app-store-connect-api/).

The public customer-review RSS URL family appears in an [Apple Developer Forums discussion](https://developer.apple.com/forums/thread/94013?answerId=742672022); that discussion is not a formal API contract. No current official pagination, page-size, availability, or complete-coverage guarantee was established.

Observed read-only live checks during this discussion:

- [Spotify US, page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=324684580/sortby=mostrecent/json): feed metadata, no review entries, empty pagination links.
- [Spotify US, without explicit page](https://itunes.apple.com/us/rss/customerreviews/id=324684580/sortby=mostrecent/json): feed metadata, no review entries, empty pagination links.
- [Yelp US, page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=284910350/sortby=mostrecent/json): feed metadata, no review entries, empty pagination links.
- A delegated check of [Spotify US, page 2](https://itunes.apple.com/us/rss/customerreviews/page=2/id=324684580/sortby=mostrecent/json) also found no review entries.

These initial observations did not establish a populated response and do not prove every feed is empty. The later live validation below supersedes that uncertainty for specific app/storefront combinations, but still does not demonstrate a dependable route to 200 arbitrary-app reviews. A zero-result feed must not be presented as proof that the app has no written reviews. No App Store page-scraping fallback has been approved.

[Apple's App Review Guidelines, section 4.5.1](https://developer.apple.com/app-store/review/guidelines/) discuss approved RSS feeds and scraping restrictions. Those guidelines alone do not establish permission for this separate research service to persist review text or send it for AI analysis; applicable source terms need verification.

### IndexedDB and keys

[OWASP's client-side database guidance](https://cheatsheetseries.owasp.org/cheatsheets/HTML5_Security_Cheat_Sheet.html#client-side-databases) identifies IndexedDB as structured browser storage, not a secret vault. Same-origin malicious JavaScript can read or modify it, and browser-profile access is another risk. Do not silently interpret approval of IndexedDB for research as approval to persist provider keys there.

For the existing local FastAPI architecture, an OS credential store accessed by the backend is the proposed persistent-secret mechanism, not browser storage. Python's [keyring documentation](https://keyring.readthedocs.io/en/latest/) lists macOS Keychain, Windows Credential Locker, and Linux Secret Service/KWallet support. Backend selection must be checked; an insecure alternate backend must not silently replace the intended store. This is a recommendation, not an implemented or approved integration.

### Python model interfaces and orchestration

[LangChain models](https://docs.langchain.com/oss/python/langchain/models) expose a common interface through `init_chat_model` and provider integration packages, including OpenAI, Anthropic, and Google. Provider capabilities and authentication are not necessarily interchangeable even when the model interface is shared.

[LangGraph](https://docs.langchain.com/oss/python/langgraph/overview) orchestrates stateful workflows and supports deterministic Python steps alongside model calls. The user's requested stack can therefore separate review fetching, per-app analysis, and comparison without adding an autonomous agent loop.

Alternatives considered for the user's Python AI SDK question: [Pydantic AI](https://ai.pydantic.dev/) provides a typed, multi-provider AI SDK; [LiteLLM](https://docs.litellm.ai/docs/) offers a unified provider-call interface using an OpenAI-style format. They are alternatives, not additional dependencies required on top of the requested LangChain/LangGraph stack.

Local retrieval operates on already acquired documents; it is not an entitlement to an upstream review dataset. A LangChain integration would still depend on the underlying source's access, availability, and terms. The user approved local embeddings and retrieval-augmented generation as support for complete-sample review analysis and review comparison.

The delegated review of LangChain's [document-loader catalog](https://docs.langchain.com/oss/python/integrations/document_loaders) and [retriever catalog](https://docs.langchain.com/oss/python/integrations/retrievers) found no documented dedicated Apple App Store review integration. This is not proof that no community package exists. The [Apify integration](https://docs.apify.com/integrations/langchain) can load an Actor's collected data, but source access and authorization remain the Actor/provider's responsibility; connector availability does not prove review coverage or permitted reuse. [Apple's website terms](https://www.apple.com/legal/internet-services/terms/site.html) also restrict automated scraping/access. Validate a specific source's provenance, coverage, freshness, and permitted storage/AI use before selecting it.

### ChatGPT identity versus model authorization

OpenAI currently documents [Sign in with ChatGPT](https://developers.openai.com/siwc/quickstart), including optional use of an eligible ChatGPT plan for authorized inference. Its quickstart distinguishes selected commercial partners in a limited trial from open-source partners and selected private clients. Identity scopes alone do not grant AI API access.

The [open-source registration/sign-in guide](https://developers.openai.com/siwc/token-sharing-open-source/sign-in) documents PKCE, a loopback callback, dynamic registration, and separate plan-usage scopes for eligible Responses API calls. This is a documented flow, not authorization to reuse Codex client credentials or copy browser cookies. Token refresh, storage, granted scopes, and inference restrictions require their own supported integration.

Repository metadata checked with `gh repo view sanketsingh27/bibi --json visibility,isPrivate,licenseInfo,url`: public repository; `licenseInfo` is null. Public visibility alone does not establish open-source licensing or eligibility for the documented flow. No successful registration, login, or authenticated inference has been exercised. Do not promise ChatGPT-plan access for Bibi until eligibility and its request contract are verified.

The [documented model/inference contract](https://developers.openai.com/siwc/token-sharing-open-source/models-and-inference) and [preview limitations](https://developers.openai.com/siwc/token-sharing-open-source/preview-limitations) apply separately from normal API-key use. The delegated source review found a Responses API flow requiring streaming and `store: false`, with unsupported fields/tools. Standard `langchain-openai` invocation has not been demonstrated to satisfy this contract. A uniform model interface does not imply uniform OAuth support; verify compatibility rather than passing a token into an arbitrary chat-model call.

### Approved local embeddings and review retrieval

The user approved creating embeddings locally after fetching written reviews, then using retrieval-augmented generation (RAG) to support review comparison alongside complete-sample analysis. [LangChain's retrieval guide](https://docs.langchain.com/oss/python/deepagents/retrieval) describes embeddings, document retrieval, and supplying the retrieved text to a model.

Approved division:

- Review analysis processes the complete fetched review sample, in batches when needed, to identify themes. Counts must be calculated from the processed records, not guessed from embedding similarity or the model's prose.
- Local embeddings support finding relevant evidence for a comparison topic. Retrieve separately for each chosen app and the selected storefront; preserve links to the original written reviews. A small similarity-selected subset must not be described as coverage of the complete sample.
- Review comparison uses the per-app analyses plus relevant written-review evidence, with the actual sample sizes and source limits visible. Missing retrieved evidence does not prove a feature or complaint is absent.
- Create both review and query embeddings with the same local embedding model/version. Persist the review-to-embedding association without replacing the original text; rebuild affected embeddings when reviews or the model change. Exact model, execution location, and index/storage design remain open.
- Local embeddings do not make generation offline. The selected external AI provider still receives any written-review text included in its analysis or comparison request.

This approach does not supply missing source access. A working, permitted way to obtain the review sample is still required. No additional chat interface or general-purpose vector database has been approved.

### Review-data service candidate checked after Q17 approval

[Appfigures Public Data Access](https://docs.appfigures.com/guides/public-data-access/) documents reviews for apps the account does not own, including country-specific access. Its [reviews endpoint](https://docs.appfigures.com/reference/reviews/) supports app and country filters, newest-first sorting, pagination, and 1–500 reviews per request. These are documented capabilities; no authenticated fetch was exercised.

Access to apps the account does not own requires the Public Data API add-on and prepaid credits. The reviewed public guide states a minimum of two credits per request, but does not establish Bibi's exact dollar cost or a reviews-specific price. It permits internal analytics/competitor research and prohibits publishing/reselling data without separate arrangements. Permission for Bibi's exact persistent-storage and external-AI workflow still needs verification; do not infer it from general internal-use language.

The subsequently checked [API terms](https://docs.appfigures.com/terms/), labelled updated April 25, 2016, explicitly restrict public data for apps the account does not own to caching for no more than 24 hours. Standard access therefore does not establish permission for the requested persistent competitor-review corpus. Different written terms would be required before choosing this source for that behavior; external-AI processing and treatment of derived embeddings/analyses also remain unconfirmed. Do not silently shorten research retention to accommodate this vendor.

This is a candidate, not a selected vendor. No account, key, purchase, pricing approval, or external integration has been authorized.

### Requested public-feed star-filter check

The user explicitly requested checking Apple's public JSON endpoint before deciding how star-based fetching works. The inspected [official customer-review API schema](https://developer.apple.com/documentation/appstoreconnectapi/get-v1-apps-_id_-customerreviews) documents `filter[rating]` with values 1–5 for the authenticated App Store Connect API. That contract does not establish support on the unauthenticated `itunes.apple.com/.../rss/customerreviews/.../json` feed. No documented public-feed rating filter was found in the sources reviewed.

Fresh read-only HTTP checks used system `curl` with certificate verification enabled:

- Yelp US (`284910350`), page 1, `sortby=mostrecent/json`: HTTP 200, zero review entries.
- The same Yelp URL with `?rating=3`: HTTP 200, zero review entries.
- The same Yelp URL with `?filter%5Brating%5D=3`: HTTP 200, zero review entries.
- Duolingo US (`570060128`), confirmed by a live Apple ID lookup: HTTP 200, zero review entries for each of four URL forms: page 1 with lowercase sort, no page with lowercase sort, no page with camelcase sort, and no page or sort.

At this initial check, the two rating query parameters were experimental probes, not documented RSS parameters. HTTP 200 and identical empty review sets did not prove either filtering support or its absence. No populated control was obtained in that round; the later validation below adds a populated control. Initial Python `urllib` requests failed local certificate-chain verification before a response; system `curl` was used without disabling TLS verification.

Decision for this design: do not rely on unsupported upstream rating parameters or promise 200 matching reviews. Fetch the available mixed-star review sample and filter stored records by their rating field. A three-star result means three-star written reviews within that sample, not all three-star App Store reviews.

### Live public-JSON validation — 2026-10-22

Result: unauthenticated Apple public JSON review access works for some app/storefront combinations. A fixed 200-review sample, complete recent history, and reliable pagination are not demonstrated.

The main session used system `curl` with normal TLS verification and parsed actual JSON review records, requiring both `im:rating` and review text. Apple ID lookups first confirmed Apple Support (`1130498044`), Reddit (`1064216828`), and Notion (`1232780281`) in the US catalog. Delegated batched lookups also confirmed these apps in GB, IN, and CA.

| Main-session request | Written reviews | Observation |
| --- | ---: | --- |
| [Apple Support US, page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1130498044/sortby=mostrecent/json) | 50 | 50 unique review IDs; complete observed text/rating/date/version fields |
| Apple Support US, each of pages 2, 3, and 4 | 0 | HTTP 200, feed metadata only despite page-1 next/last links |
| [Notion US, page 1](https://itunes.apple.com/us/rss/customerreviews/page=1/id=1232780281/sortby=mostrecent/json) | 50 | 50 unique review IDs |
| Notion US, each of pages 2 and 3 | 0 | HTTP 200, feed metadata only |
| [Notion US, page 4](https://itunes.apple.com/us/rss/customerreviews/page=4/id=1232780281/sortby=mostrecent/json) | 50 | 50 additional IDs, no overlap with page 1; older dates and gaps in intervening pages |
| [Notion CA, no-page form](https://itunes.apple.com/ca/rss/customerreviews/id=1232780281/sortby=mostrecent/json) | 50 | 50 unique IDs, no overlap with the 100 observed Notion US IDs |
| Notion CA, page 2 JSON | 0 | HTTP 200, feed metadata only |
| Reddit US, page 1 JSON | 0 | HTTP 200, feed metadata only |

The two populated US page-1 samples each contained `id`, `im:rating`, `title`, `content`, `updated`, and `im:version` in all 50 records. All text bodies were non-empty, dates parsed, and star values were valid integers from 1 through 5. The four main-session populated JSON pages were each ordered newest-first by their observed `updated` values. This is observed behavior, not an Apple contract.

Exact local three-star filtering on the live page-1 data returned 3 Apple Support US reviews and 6 Notion US reviews. Embeddings are not needed for this numerical filter. Adding either `?rating=3` or `?filter%5Brating%5D=3` to the populated Apple Support URL returned zero review records. Neither probe supplied usable star-filtered results; these undocumented parameters must not be relied on.

Page-1 JSON pagination links pointed to XML URLs with a `urlDesc` query referring to JSON. Following the actual Apple Support US page-2 XML link returned zero Atom review entries. Keeping the query while changing the suffix to JSON also returned zero reviews. Direct raw-XML checks of the GB Apple Support and CA Notion page-2 links likewise found zero `atom:entry` and zero rating records. A delegated rendered-XML interpretation initially reported ten reviews; that claim was retracted and is not counted as evidence.

The bounded delegated non-US probe found populated GB Apple Support and CA Notion page-1 feeds, with the other seven app/storefront combinations empty. A subsequent main-session raw request confirmed the CA Notion sample but returned an empty GB Apple Support feed. This difference establishes neither a caching cause nor dependable availability; retain the observations separately.

Storefront means the requested URL territory and associated listing context. Review entries have no independent reviewer-country field; do not infer a reviewer's residence. Do not merge countries silently. The CA and US Notion samples had distinct IDs in this check.

Conclusions for specification: the source is technically usable on a best-effort basis, local star filtering is proven on real data, and partial/unavailable states are necessary. An empty intermediate page is not proof that later pages contain no reviews: Notion US page 4 was populated despite pages 2–3 being empty. The original approximately-200-review expectation therefore needs an explicit sample-size and bounded-fetch decision; do not silently reduce it to 50 or claim the observed 100 Notion US reviews are a contiguous latest-100 sample.

Upstream implementation references: [`appler` review-fetching source](https://rdrr.io/cran/appler/src/R/reviews.R) constructs the public URL and maps XML next links to JSON; [AWS's mobile-review sample](https://github.com/aws-samples/sample-voice-of-customer-datalake/blob/main/docs/mobile-app-reviews.md) describes 50-per-page/10-page assumptions. These are implementation evidence, not Apple guarantees. Direct access to the cited Apple Developer Forums thread was blocked by its verification page during this round.

No application code, installed dependencies, provider accounts, paid services, or permanent tests were changed. No AI analysis or embeddings were executed; this investigation validates source data and exact local rating filtering only.

### OpenRouter selection and evidence

The user's Q26 answer selects OpenRouter key-based access with model selection, replacing the earlier direct-provider credential choice for this feature. LangChain documents a dedicated [`ChatOpenRouter` integration](https://docs.langchain.com/oss/python/integrations/chat/openrouter/) in `langchain-openrouter`; no second gateway abstraction is required.

OpenRouter documents a [model catalog](https://openrouter.ai/docs/api/api-reference/models/list-all-models-and-their-properties.md) and [credit/rate limits](https://openrouter.ai/docs/api_reference/limits.md). A read-only, unauthenticated live request to `https://openrouter.ai/api/v1/models?output_modalities=text&limit=3` returned HTTP 200 with three model records, each containing an ID, display name, pricing, context length, and supported-parameter metadata. This proves catalog access only, not authenticated inference, account eligibility for a model, or integration correctness.

[OpenRouter's data-collection policy](https://openrouter.ai/docs/guides/privacy/data-collection.md) distinguishes its own opt-in prompt logging from request metadata. [Provider policies](https://openrouter.ai/docs/guides/privacy/provider-logging.md) differ for training and retention. Reviews sent for analysis pass through OpenRouter and an upstream model provider; a single key does not make processing local or establish identical privacy terms across models. Local embeddings remain local and must not be silently moved to OpenRouter's embedding service.

The Apple review-page request schedule and OpenRouter inference limits are separate. Paced batches and honoring rate-limit responses can limit request pressure, but no claim that batching prevents rate limiting is justified. No paid inference, credentials access, dependency installation, or application code change was performed.

### Jev suitability check requested with Q28

The user asked whether a decision model such as Jev could make quick decisions, while explicitly retaining one model for all tasks for now. Research does not authorize a second model, automatic model routing, new classification scope, or paid inference.

[OpenRouter's Jev integration documentation](https://openrouter.ai/docs/guides/community/jev) and [TypeSafe's System One documentation](https://docs.typesafe.ai/concepts/system-one) describe typed decisions rather than prose: choosing a category, answering a yes/no question with a probability, or scoring against defined levels. Jev is not a drop-in report-writing chat model and does not supply written explanations. Its [confidence documentation](https://docs.typesafe.ai/confidence) explains that confidence derives from its probability distribution and thresholds require validation on the actual use case; confidence is not proof that an individual decision is correct.

A live, unauthenticated request to `https://openrouter.ai/api/v1/models?output_modalities=decisions&q=jev&limit=10` returned HTTP 200 and catalog records including `typesafe/jev-1.14`, `~typesafe/jev-latest`, and `typesafe/jev-1.13`. The records identify their output modality as `decisions`. This verifies listing metadata, not account-specific access, successful inference, accuracy, latency, or cost advantage in Bibi. No inference request or benchmark was run.

OpenRouter documents separate Decisions/System One API surfaces for Jev, authenticated with the same OpenRouter key. Do not assume that selecting it in the normal text-model picker makes it work through the existing proposed `ChatOpenRouter` report-generation path.

Potential future evaluation tasks are classifying a written review as a complaint or feature request, or assessing whether an app is a same-problem candidate. These would need representative examples and measured error/latency/cost before adoption. Exact star filtering, review counts, deduplication, fetch limits, and rate-limit handling are deterministic code, not decision-model tasks. Full review analysis and evidence-linked comparison still require a generative model.

[Jev Router](https://openrouter.ai/docs/guides/routing/routers/jev-router) is different from the decision model: it chooses other models and reasoning effort dynamically. It is not equivalent to the agreed single, explicitly selected model.

Recommendation accepted by the user's “ok” response: keep one selected text model through OpenRouter for this feature, with no Jev model or Jev Router integration. The suitability check is complete; a later benchmark would need separate approval and a concrete classification task.

## Confirmation gate

Shared understanding was confirmed with “confirm design”, followed by **Approve map and tests**. Specification synthesis, publication, and publication verification are complete. Ask the user to review and approve the published specifications before drafting implementation tickets. Do not start implementation until the later project gates are satisfied.

## Publication evidence

| Specification | Published issue |
| --- | --- |
| Parent: local app details, review analysis, and competitor comparison | [#20](https://github.com/sanketsingh27/bibi/issues/20) |
| AI runtime | [#21](https://github.com/sanketsingh27/bibi/issues/21) |
| App details | [#22](https://github.com/sanketsingh27/bibi/issues/22) |
| Review library | [#23](https://github.com/sanketsingh27/bibi/issues/23) |
| Review analysis | [#24](https://github.com/sanketsingh27/bibi/issues/24) |
| Competitor comparison | [#25](https://github.com/sanketsingh27/bibi/issues/25) |

All six issues were fetched back from GitHub. Each complete body matches its local specification, has the seven required sections and continuously numbered user stories, remains open, and has the `ready-for-agent` label. That label does not authorize implementation.

Native relationships were fetched back and verified: #20 has children #21–#25; #23 is blocked by #22; #24 is blocked by #21 and #23; #25 is blocked by #22 and #24. These are specification dependencies, not implementation tickets or branch assignments.

No application code was changed, and no application tests, builds, or live AI inference were run for specification publication. Source-use permission, provider credentials and credits, secure credential storage, and local embedding setup remain explicit implementation prerequisites rather than claimed verification results.
