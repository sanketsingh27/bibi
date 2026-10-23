# Capability Map: Local App Research

Status: capability boundaries and testing approach approved by the user through **Approve map and tests**, following **confirm design**. This map is not approval of the specifications or implementation.

The existing Next.js/FastAPI app remains one local application. These IDs identify capabilities, not separately deployed services.

| Module ID | Responsibility | Depends on | Build stage | Specification |
| --- | --- | --- | --- | --- |
| `app-details` | Exact listing lookup, App Store-style detail page, and return-to-search state | Existing app discovery | 1 | [Local](SPEC-app-details.md) · [#22](https://github.com/sanketsingh27/bibi/issues/22) |
| `ai-runtime` | OpenRouter key/settings, OS credential storage, compatible model selection, shared inference boundary | Existing local app | 1 | [Local](SPEC-ai-runtime.md) · [#21](https://github.com/sanketsingh27/bibi/issues/21) |
| `review-library` | Public JSON review collection, bounded progress/cancellation, IndexedDB research, star filtering, refresh and deletion | `app-details` | 2 | [Local](SPEC-review-library.md) · [#23](https://github.com/sanketsingh27/bibi/issues/23) |
| `review-analysis` | Complete-sample and filtered analysis, local embeddings/RAG, evidence links, explicit updates | `review-library`, `ai-runtime` | 3 | [Local](SPEC-review-analysis.md) · [#24](https://github.com/sanketsingh27/bibi/issues/24) |
| `competitor-comparison` | Metadata-based suggestions, manual app selection, evidence-linked side-by-side comparison | `app-details`, `review-analysis` | 4 | [Local](SPEC-competitor-comparison.md) · [#25](https://github.com/sanketsingh27/bibi/issues/25) |

Stage 1 capabilities may be specified independently. Later stages require the provider contracts indicated above. All five capabilities are required; this order does not narrow the approved end-to-end design.

## Integration contract

- [Parent specification, local copy](docs/app-research-spec.md) / [published #20](https://github.com/sanketsingh27/bibi/issues/20) defines shared identities, API operations, persistence and evidence invariants. Module specifications must agree with that contract.
- Existing app discovery remains usable without AI credentials, a local embedding model, or saved research. Its search/catalog contract is retained.
- The browser owns persisted research in IndexedDB. FastAPI performs upstream calls and local embedding work. Device credentials use the OS credential store, not browser storage. There is no server research database.
- The review-library capability introduces the transient operation coordinator and public operation protocol used later by analysis/comparison; ai-runtime Settings/catalog endpoints do not depend on that coordinator.
- Review-source limits remain visible. The first target is 200 written reviews; the user may request 500. Neither is a guarantee. Star filters are exact local record filters.
- One selected OpenRouter text model handles AI tasks. LangChain/LangGraph orchestrate bounded workflows, not autonomous tool agents. Local embedding generation is separate and remains on-device. Jev and model routers are excluded.

## Approved verification boundaries

Reuse the real FastAPI HTTP API with pytest/HTTPX as the primary automated seam, controlling external responses/time and isolating credential storage. Verify browser state/IndexedDB, real local embeddings, and authorized inference through actual runtime scenarios. No new frontend test framework is proposed.

No implementation is authorized. Published specifications require user approval before ticket drafting, ticket approval/publication, and fresh-session implementation handoffs.
