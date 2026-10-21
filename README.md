# Bibi — local App Store discovery

Tickets [#15](https://github.com/sanketsingh27/bibi/issues/15) and [#19](https://github.com/sanketsingh27/bibi/issues/19), under [spec #14](https://github.com/sanketsingh27/bibi/issues/14), provide a separate local keyword-discovery application with transient metadata caching and identical-request sharing. `landing-page/` remains the existing informational site, unchanged.

## Requirements and setup

Use Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 22+ and npm 11. The verified environment used Python 3.12.4, uv 0.11.7, Node.js 25.9.0 and npm 11.21.0. No Apple credential, database, account, or environment file is required. Apple connectivity is needed only for live searches, not the API suite.

From `backend/`:

```sh
uv sync --frozen
source .venv/bin/activate
python -m pytest
python -m uvicorn bibi.main:app --host 127.0.0.1 --port 8000 --workers 1
```

In a second terminal, from `frontend/`:

```sh
npm ci --ignore-scripts
export NEXT_TELEMETRY_DISABLED=1
npm run build
npm run dev -- --hostname 127.0.0.1 --port 3000
```

Open **http://127.0.0.1:3000**. To exercise the production frontend instead of the dev server, stop the dev server and run:

```sh
npm run start -- --hostname 127.0.0.1 --port 3000
```

The API must remain running. These commands deliberately bind both applications to loopback. One backend worker/process is required: multiple workers or public hosting are unsupported because the cache, pending operations, and request budget are process-local. Restarting the API clears all three.

The frontend's `.npmrc` disables dependency lifecycle scripts. The locked install and Next.js build work with scripts disabled; do not blanket-enable installation scripts. `backend/uv.lock` and `frontend/package-lock.json` pin each independent installation boundary.

## Searching

The screen starts blank in the United States storefront. Type a market phrase, then use **Search** or **Enter**. Typing and focusing never search. Results retain Apple's returned order, show at most 50 matches, and are not a complete App Store catalog or a classified competitor set.

Each row identifies the name, developer, numeric Apple ID, and original safe listing link. Missing information is marked unavailable. Loading, no matches, invalid input, rate limits, timeout, and upstream failure have separate states. Manual Retry repeats the failed submitted phrase/storefront even if the input contains a newer draft. A newer submission invalidates older responses, including when the newer input is invalid.

The submitted query/storefront, limited-match count, metadata fetch time and cache status belong to the displayed response. FastAPI caches successful normalized metadata, including empty results, for **24 hours from successful fetch completion**. Repeating a fresh search displays **Cached metadata**, with its original fetch time. New upstream fetches and callers joining an identical pending operation display **Fresh from Apple · Not cached**. Reload clears the page, not the running backend's cache.

Cache identity includes the whitespace-normalized phrase (without case-folding or rewriting), country, limit, and fixed Apple search parameters. Countries and limits remain isolated. At exactly 24 hours, the entry expires; a cache hit never extends its lifetime. Expired results are not returned after a failed refresh. Failures are not cached; retry requires an explicit new submission and is still subject to the budget.

There are no automatic retries, background searches, polling, queues, fallback data, saved browser search state, or search phrases in the page URL. Browser/HTTP/Next.js response caching remains disabled; FastAPI is the only metadata cache. Only listing metadata and URLs are cached, never artwork files.

App-name confirmation, the country-picker interaction, and icon/category/ratings/copy UI belong to separate tickets and are intentionally absent here. The API already supplies their complete normalized metadata contract and storefront catalog.

## API

The browser uses same-origin `/api/v1/apps/*`; Next.js rewrites that fixed path to `http://127.0.0.1:8000`. Only FastAPI calls `https://itunes.apple.com/search`. No caller-supplied upstream URL, Apple Lookup calls, reviews, or AI work is supported. External App Store links are ordinary navigation, not API searches.

### `GET /api/v1/apps/storefronts`

Returns `{defaultCountry: "us", storefronts: [{code, name}, ...]}` without Apple traffic or budget use. Backend validation and the frontend's initial country use this one catalog.

`backend/bibi/storefronts.py` is a static snapshot derived from the **App Store** entries of [Apple Media Services availability](https://support.apple.com/en-us/118205), retrieved 2026-10-22, not from all ISO countries or availability of unrelated media services. It includes US and India. Apple's Kosovo storefront uses the ISO user-assigned code `xk`. Updates require checking that source and the API behavior together, not live scraping per request.

### `GET /api/v1/apps/search`

| Input | Contract |
| --- | --- |
| `q` | Required; collapse/trim whitespace, then 2–100 Unicode code points; no semantic or case rewriting |
| `country` | Trim/lowercase; must occur in the static catalog; defaults to `us`, never substitutes a country |
| `limit` | Integer 1–50; defaults to 50 |

Unknown and repeated parameters are rejected. No offset/pagination feature is provided. The Apple request fixes `media=software`, `entity=software`, `lang=en_us`; see [Apple's Search API reference](https://performance-partners.apple.com/search-api).

A successful response has `query`, `country`, UTC ISO-8601 `fetchedAt`, `cached`, and `results`. Every result contains:

- `appId`: positive JavaScript-safe integer; `country`: requested storefront.
- `name`, `developer`, `category`: plain-text strings or null. Markup-like text is never interpreted as HTML.
- `iconUrl`: safe HTTPS artwork URL, using the 60px fallback when the 100px URL is unavailable/unsafe; otherwise null. No artwork is rendered in #15.
- `averageRating`: finite number in 0–5 or null; `ratingCount`: nonnegative JavaScript-safe integer or null. Genuine zero stays zero, and a rating is never inferred from its count.
- `storeUrl`: safe HTTPS link on `apps.apple.com` or `itunes.apple.com`, without credentials or nonstandard ports; otherwise null.

Non-software records and invalid IDs are filtered. The first usable record per ID wins, upstream order is retained, and results are capped at `limit`. Missing/invalid optional metadata becomes null. Invalid JSON, an invalid envelope/count/results shape, or non-object result entries are failures, not an empty catalog response.

### Budget and failure contract

The single process reserves at most **10 dispatched attempts in a rolling 60 seconds**, including failures and simultaneous requests. It checks fresh cache first, then joins identical pending work, then reserves budget for a new dispatch. Hits and joiners use no new slot and still work while the budget is exhausted; a different uncached identity is rejected immediately. Every shared Apple operation has an **8-second overall deadline**, including reading the body, with TLS verification and no automatic retries or redirect following.

Identical concurrent misses share one Apple operation and receive the same success or structured failure. Joiners receive `cached=false`, not a cache hit. Completion or failure removes pending work so a later manual retry can proceed. A disconnected browser caller does not cancel work needed by other tabs; application shutdown cancels any abandoned pending operation before closing the Apple client.

Errors have one shape: `{error: {code, message}}`. Messages never expose raw upstream bodies or exceptions. API responses include `Cache-Control: no-store`.

| HTTP | `error.code` | Retry indication |
| --- | --- | --- |
| 422 | `VALIDATION_ERROR` | No Apple dispatch |
| 429 | `SEARCH_RATE_LIMITED` | `Retry-After`: ceiling of seconds until the next eligible local slot |
| 429 | `UPSTREAM_RATE_LIMITED` | Valid Apple integer-seconds or HTTP-date `Retry-After` is preserved; absent/invalid remains absent |
| 502 | `UPSTREAM_ERROR` | Manual retry only |
| 504 | `UPSTREAM_TIMEOUT` | Manual retry only |

FastAPI's generated schema is at http://127.0.0.1:8000/docs.

## Verification

From `backend/`, with `.venv` activated, `python -m pytest` runs the offline behavioral API suite. It uses the real FastAPI boundary/service and controls only the Apple HTTPX transport and time. Tests cover input/catalog agreement, ordering/filtering/deduplication/capping, nullable metadata and safe URLs, empty versus malformed results, failures/429/timeout, failed-attempt accounting, exact rolling-window and 24-hour boundaries, country/limit/case/whitespace identity, shared success/failure, manual recovery without stale fallback, cache/join precedence under exhausted budget, fresh application reset, disconnect/shutdown handling, and the overall deadline during a blocked body read. Concurrency uses deterministic events and controlled clock reads, not sleeps. There is no separate helper/UI unit-test seam.

From `frontend/`, run `npm run build` and `npm audit`. From the repository root, with both servers running:

```sh
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/search?q=adhd%20planner&country=us&limit=50'
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/storefronts'
```

Browser runtime acceptance is separate from the suite/build:

1. Open the blank US-scoped screen. Focus/type `adhd planner` and confirm no search request in browser Network. Submit using Search, then submit another phrase using Enter. Observe actual populated Apple results, not a fixed expected count.
2. Open an original listing; verify navigation to Apple's listing and no review/research work. Check the limited-match count, submitted phrase/storefront and fresh/not-cached timestamp. Repeat `adhd planner`: observe `cached=true`, unchanged `fetchedAt`, **Cached metadata**, and no second Apple dispatch. Reload: the screen resets, but resubmitting still hits the backend cache. Stop/restart only your API process with the documented command; the next search must fetch again with `cached=false`.
3. Submit rapidly changing phrases. Older responses must not overwrite the newer submission. Reload and confirm blank input, no result rows, US context and no page search parameters.
4. For deterministic failures, wrap the real `create_app(apple_transport=..., clock=...)` in a **temporary local-only runner** using `httpx.MockTransport`, as the API tests do. Start that runner on port 8000 instead of the live backend, leaving the real Next.js path unchanged. Exercise successful empty, invalid query, Apple 429 with/without Retry-After, 503, and a blocked operation hitting the real 8-second deadline. Do not add fixture endpoints or fallbacks to the application.
5. In that controlled runner, hold an older response behind an event, complete a newer search, then release the old response. Fail a submitted phrase, edit the draft, and use Retry: the request must still contain the failed phrase. Admit ten controlled dispatches (including failures), observe the next local 429 without an eleventh Apple dispatch, advance the controlled clock and retry manually. Inspect network/dispatch logs for no automatic retries. Check keyboard operation and 320/768/1024/1440px layouts.

For #19's two-tab scenario, use that same temporary runner with a representative Apple response held behind an event. Submit the same uncached phrase from two browser tabs before releasing it; observe one Apple dispatch and identical `fetchedAt`/results with `cached=false` for both. Repeat with a held Apple failure: both tabs must receive the structured error, and a manual retry after recovery must make a new dispatch and succeed. Do not replace the search service or add a fixture endpoint. The offline API suite proves TTL/budget timing without waiting a day or exhausting Apple's live service.

Implementation evidence and final acceptance/integration status are tracked on [#15](https://github.com/sanketsingh27/bibi/issues/15) and [#19](https://github.com/sanketsingh27/bibi/issues/19). Live counts and catalog ordering change over time; an upstream failure or zero matches is not proof of the populated flow.
