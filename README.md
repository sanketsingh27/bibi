# Bibi — local App Store discovery

Tickets [#15](https://github.com/sanketsingh27/bibi/issues/15), [#16](https://github.com/sanketsingh27/bibi/issues/16), [#17](https://github.com/sanketsingh27/bibi/issues/17), [#18](https://github.com/sanketsingh27/bibi/issues/18), and [#19](https://github.com/sanketsingh27/bibi/issues/19), under [spec #14](https://github.com/sanketsingh27/bibi/issues/14), provide local keyword/app-name discovery, storefront switching, explicit confirmation, listing metadata, app-ID copying, transient metadata caching, and identical-request sharing. `landing-page/` remains the existing informational site, unchanged.

## Requirements and setup

Use Python 3.12+, [uv](https://docs.astral.sh/uv/), Node.js 22+ and npm 11. The verified environment used Python 3.12.4, uv 0.11.7, Node.js 25.9.0 and npm 11.21.0. No Apple credential, database, account, or environment file is required. Apple connectivity is needed only for live searches, not the API suite.

From the repository root:

```sh
./dev install
./dev
```

`install` runs the locked backend and frontend installs with npm lifecycle scripts
disabled; it starts no servers. Normal startup skips installation and runs both
servers in the invoking terminal, with their live output visible. Open the printed
**Frontend** URL. The launcher prefers frontend port **3000** and backend port
**8000**, choosing distinct available alternatives when either port is occupied.
Both API prefixes automatically forward to the selected backend port.

Press **Ctrl+C** to stop both servers and their child processes. SIGTERM or either
server exiting also cleans up this invocation; unrelated listeners are preserved.
Both servers bind only to `127.0.0.1`, with one backend worker. `./dev.sh` supports
the same commands. Either entrypoint also works by absolute path from another
directory. Missing tools/dependencies or unsupported arguments produce guidance
and a nonzero exit.

For manual startup, from `backend/`:

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

The screen starts blank in **Keyword** mode in the United States storefront. Choose **Keyword** for a market phrase or **App name** for a known product, then use **Search** or **Enter**. Typing and focusing never search. Both modes use the same search endpoint with only `q`, `country`, and `limit`; mode is browser presentation, not inferred intent or an exact-title algorithm. Results retain Apple's returned order, show at most 50 matches, and are not a complete App Store catalog or a classified competitor set.

Each row identifies the name, developer, numeric Apple ID, category, average rating (out of five), rating count, available icon, and original safe listing link. Missing information is marked unavailable. A missing rating is not a zero-star score; a genuine zero rating/count stays zero. Rating counts are ratings, not written reviews, and belong to the displayed country storefront rather than global totals. Loading, no matches, invalid input, rate limits, timeout, and upstream failure have separate states. Manual Retry repeats the failed submitted phrase/storefront even if the input contains a newer draft. A newer submission invalidates older responses, including when the newer input is invalid.

In **App name** mode, compare candidate names and developers, then choose **Confirm app** on the intended listing. Keyword results offer **Open app**. Both actions open the exact app's detail page; even one candidate requires explicit selection. The bookmarkable URL contains only `appId` and `country`, for example `/?appId=1480220328&country=us`. Reload reopens that identity. The detail page shows real listing identity, storefront, listing ratings, category, available description/screenshots, formatted price, version, release dates/notes, original listing link and fetch/cache status. Missing fields remain explicitly unavailable. Screenshots load directly from safe source URLs, each beside an original-listing App Store badge, under the existing [Apple promotional-content policy](https://performance-partners.apple.com/search-api). No artwork files are stored by the application. No reviews or AI operations start.

**Analysis**, **Reviews**, and **Competitors** tabs support Arrow Left/Right and Home/End with one tab stop and a focusable active panel. Analysis opens first. They describe the currently unavailable dependent research capabilities and prerequisites; tab changes send no collection or paid request.

Successful detail snapshots persist as metadata/URLs in this browser’s IndexedDB (`bibi-detail-snapshots`, `listings` store), keyed by app ID and storefront. If live lookup fails, a validated same-identity snapshot appears with a **Saved snapshot · Live lookup failed** notice and its original fetch time; it is never labelled fresh. Invalid identity data cannot supply a fallback. Untrusted stored fields and URLs are validated again before display. Storage failure is visible and does not discard live details or overwrite an earlier successful snapshot. Browser storage is local to the origin/device and may be cleared or evicted; it does not persist search sessions, review samples or reports.

**Back to search** and browser Back preserve the current session's submitted phrase/storefront/results, chosen mode and unfinished draft without another search request. Keyboard selection moves focus into the detail page; return restores the selection button. A direct bookmark/reload retains app/storefront identity, not a persisted search session. Obsolete detail responses are aborted and ignored.

The submitted query/storefront, limited-match count, metadata fetch time and cache status belong to the displayed response. FastAPI caches successful normalized metadata, including empty results, for **24 hours from successful fetch completion**. Repeating a fresh search displays **Cached metadata**, with its original fetch time. New upstream fetches and callers joining an identical pending operation display **Fresh from Apple · Not cached**. Reload clears the search session, not detail URL identity or the running backend's cache.

Cache identity includes the whitespace-normalized phrase (without case-folding or rewriting), country, limit, and fixed Apple search parameters. Countries and limits remain isolated. At exactly 24 hours, the entry expires; a cache hit never extends its lifetime. Expired results are not returned after a failed refresh. Failures are not cached; retry requires an explicit new submission and is still subject to the budget.

There are no automatic retries, background searches, polling, queues, fabricated fallback data, saved browser search state, or search phrases in the page URL. Browser/HTTP/Next.js response caching remains disabled; FastAPI holds the transient source cache, separate from explicitly labelled browser-saved detail snapshots. Only listing metadata and URLs are cached, never artwork files.

The labelled **Country storefront** picker loads readable names/codes from the backend catalog, initially selecting **United States (US)** with **India (IN)** available. Before any submission, changing country makes no search request. After a submission, it reruns only the last submitted phrase in the new country, preserving unfinished input. The picker is outside the submission form so using Enter on it cannot submit a draft. Loading and errors identify their submitted phrase/country; old responses cannot replace newer identities. Empty or unavailable results never substitute another country or app. If the catalog cannot load, search and the picker remain disabled with an explicit error; reload after restoring the API. Reload of the search page resets to US, blank input and Keyword mode.

### Metadata, clipboard, and artwork

Keyword results, App name candidates, and the exact detail header use the same metadata, copy, artwork, and badge presentation. Detail lookup fetches the explicitly selected numeric identity in its storefront.

**Copy app ID** writes only the numeric Apple app ID using the browser Clipboard API. The row announces success only after that operation resolves; denial, unavailable clipboard support, or another failure produces an accessible failure message and manual-copy guidance. Use a secure browser context (loopback is supported) and allow clipboard access when prompted. Search, copy, and original-listing links are keyboard-operable. Listing names, developers, and categories are rendered as text, never HTML.

Icons load directly in the browser from normalized HTTPS artwork URLs; the backend does not fetch or store artwork files. An icon is displayed only when a safe original Apple listing link is also available, with a proximate linked **Download on the App Store** badge. Without the listing link, the icon is withheld and marked unavailable rather than inventing a destination. Failed icon loads are also marked unavailable.

`frontend/public/download-on-the-app-store.svg` is Apple's unmodified preferred black badge, obtained from [Apple's official asset](https://developer.apple.com/assets/elements/badges/download-on-the-app-store.svg). Each listing promotion uses a 40px-high badge with at least 10px clear space, linked to that listing; the footer credits Apple's trademarks. See the [Search API promotional-content terms](https://performance-partners.apple.com/search-api) and [App Store marketing guidelines and applicable artwork license](https://developer.apple.com/app-store/marketing/guidelines/). Artwork is used to promote its original listing, not Bibi or unrelated services; private/local use does not waive Apple's terms or confer additional permissions. This implementation is not a legal clearance or Apple endorsement.

## API

The browser uses same-origin `/api/v1/apps/*` and `/api/v1/ai/*`; Next.js rewrites both fixed paths to the local FastAPI server. The launcher supplies `BIBI_BACKEND_PORT`; manual startup defaults to `http://127.0.0.1:8000`. FastAPI calls Apple's fixed search and lookup endpoints and stores the OpenRouter key only in the macOS Keychain. There are no caller-supplied upstream URLs, review fetches, model catalog, or inference operations in this slice. External App Store links are ordinary navigation, not API searches.

### Secure OpenRouter key Settings

The Settings panel accepts one write-only OpenRouter key, replaces it, and removes it. The backend stores it under the app-owned `Bibi OpenRouter` Keychain service; it never uses a file or browser-storage fallback. `GET /api/v1/ai/settings` returns only `hasKey`, `selectedModelId` (`null` in this slice), and `storeStatus` (`available` or `unavailable`). `PUT /api/v1/ai/settings` accepts only `apiKey`; `DELETE /api/v1/ai/key` is idempotent. Locked or unavailable Keychain operations return `CREDENTIAL_STORE_UNAVAILABLE`; rejected local mutation contexts return `LOCAL_REQUEST_FORBIDDEN`. Saving, checking, or removing the key makes no inference request. Model selection and inference are separate tickets.

Credential mutations require a loopback Host and reject hostile Origin or Fetch Metadata before request-body validation. Start the API and frontend using the commands above; the Keychain must be available on macOS. Do not enter a real key when exercising test flows; the offline API tests use an isolated in-memory credential store.

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
- `iconUrl`: safe HTTPS artwork URL, using the 60px fallback when the 100px URL is unavailable/unsafe; otherwise null. The browser renders it only with an available original-listing badge.
- `averageRating`: finite number in 0–5 or null; `ratingCount`: nonnegative JavaScript-safe integer or null. Genuine zero stays zero, and a rating is never inferred from its count.
- `storeUrl`: safe HTTPS link on `apps.apple.com` or `itunes.apple.com`, without credentials or nonstandard ports; otherwise null.

Non-software records and invalid IDs are filtered. The first usable record per ID wins, upstream order is retained, and results are capped at `limit`. Missing/invalid optional metadata becomes null. Invalid JSON, an invalid envelope/count/results shape, or non-object result entries are failures, not an empty catalog response.

### `GET /api/v1/apps/{appId}?country=...`

Requires a positive safe-integer numeric Apple app ID and an explicit supported lowercase storefront; invalid, missing, unknown or repeated inputs fail before Apple dispatch. Calls Apple's fixed `/lookup` endpoint with `id`, `country`, `entity=software` and `lang=en_us`. Only a software record with exactly the requested integer ID is returned. No matching record returns HTTP 404 `APP_UNAVAILABLE`, without country or name substitution. Malformed source responses remain upstream failures.

The response contains the listing fields above plus original `fetchedAt` and `cached`. Lookup cache/pending identity is the app ID and country, separate from search identity. Both operations share the same ten-dispatch rolling budget, eight-second deadline, 24-hour metadata cache policy and identical-request sharing. Static search/catalog routes remain available without AI configuration. Full metadata galleries, tabs and saved-research fallback are separate work.

### Budget and failure contract

The single process reserves at most **10 dispatched attempts in a rolling 60 seconds**, including failures and simultaneous requests. It checks fresh cache first, then joins identical pending work, then reserves budget for a new dispatch. Hits and joiners use no new slot and still work while the budget is exhausted; a different uncached identity is rejected immediately. Every shared Apple operation has an **8-second overall deadline**, including reading the body, with TLS verification and no automatic retries or redirect following.

Identical concurrent misses share one Apple operation and receive the same success or structured failure. Joiners receive `cached=false`, not a cache hit. Completion or failure removes pending work so a later manual retry can proceed. A disconnected browser caller does not cancel work needed by other tabs; application shutdown cancels any abandoned pending operation before closing the Apple client.

Errors have one shape: `{error: {code, message}}`. Messages never expose raw upstream bodies or exceptions. API responses include `Cache-Control: no-store`.

| HTTP | `error.code` | Retry indication |
| --- | --- | --- |
| 404 | `APP_UNAVAILABLE` | Exact listing absent in the requested storefront |
| 422 | `VALIDATION_ERROR` | No Apple dispatch |
| 429 | `SEARCH_RATE_LIMITED` | `Retry-After`: ceiling of seconds until the next eligible local slot |
| 429 | `UPSTREAM_RATE_LIMITED` | Valid Apple integer-seconds or HTTP-date `Retry-After` is preserved; absent/invalid remains absent |
| 502 | `UPSTREAM_ERROR` | Manual retry only |
| 504 | `UPSTREAM_TIMEOUT` | Manual retry only |

FastAPI's generated schema is at http://127.0.0.1:8000/docs.

## Verification

From the repository root, `backend/.venv/bin/python -m unittest discover -s tests -p test_dev_launcher.py -v`
runs the launcher checks in temporary projects, including installation, port
conflicts, signals, server failures, and cleanup without stopping unrelated listeners.

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

For [#16](https://github.com/sanketsingh27/bibi/issues/16), also verify:

1. Search `adhd planner` through the real app. Inspect category, average rating, rating count, storefront scope, loaded artwork, and its adjacent approved badge. Open the badge and verify the corresponding original Apple listing.
2. Use Tab and Enter/Space to copy an app ID, then paste into a plain-text input: the exact digits must match the displayed ID. Deny clipboard write permission and copy again: observe failure rather than success in the row's live status region.
3. Through the same temporary `create_app(apple_transport=httpx.MockTransport(...))` runner described above, return missing optional metadata, null average with zero count, genuine zero average/count, unsafe artwork/listing URLs, a safe artwork URL without a safe listing link, and an unsafe 100px artwork URL with a safe 60px fallback. Confirm explicit unavailable states, preserved zeros, no executable unsafe links, and artwork only alongside an original-listing badge. Include HTML-like listing text and confirm literal text, not execution.
4. Inspect narrow and wide layouts at 320/768/1024/1440px and the accessibility tree. Controlled upstream data is verification-only: never add a fixture endpoint, production fallback, or alternate UI test suite.

For [#31](https://github.com/sanketsingh27/bibi/issues/31), which extends #17's confirmation flow, verify through both real applications (no separate UI/helper test suite):

1. Submit a keyword search. Edit the input without submitting, then explicitly **Open app** on the intended listing. Verify the URL, header, numeric app ID and storefront match that listing.
2. Use **Back to search**. Verify the same submitted phrase, result IDs, storefront, mode and unfinished draft, with no additional search request. Repeat using browser Back.
3. Repeat in **App name** mode with similarly named candidates from different developers. Choose the second explicitly with **Confirm app**; never auto-select a candidate. Back must retain the candidate set and draft.
4. Reload the detail URL and open it as a bookmark. Verify the exact ID/storefront remains; a reloaded bookmark does not reconstruct a prior search session.
5. Through an external `create_app(apple_transport=httpx.MockTransport(...))` runner, exercise unavailable/mismatched software, invalid identity, missing values, unsafe URLs and markup-like text. Observe honest failure/unavailable states and literal text. Hold an old lookup, return and choose another app; an obsolete result must not replace the current identity.

From `backend/`, run `.venv/bin/python -m pytest -q tests/test_app_details.py` and `.venv/bin/python -m pytest -q`; from `frontend/`, run `npm run build`. Check selection/back focus, null/zero listing ratings, original-listing badge and 320/768/1440px layouts. Selection adds only an exact metadata lookup; searches/typing must not dispatch reviews or AI work.

For [#18](https://github.com/sanketsingh27/bibi/issues/18), verify storefront transitions through the production app (`npm run build`, then `npm run start -- --hostname 127.0.0.1 --port 3000` from `frontend/`, with the documented single-worker API running):

1. On a fresh page, type an unfinished phrase, keyboard-select India and press Enter while focused on the picker. Verify zero search requests, then return to US. Confirm the options match `/api/v1/apps/storefronts`; no unsupported code or silent fallback is offered.
2. In App name mode, submit `Tiimo`, confirm a candidate, return to search, then type a different draft without submitting. Change to India: request `q=Tiimo&country=in&limit=50`, retain the draft, clear confirmation, and show only Indian candidates/metrics. Keyboard Enter on the picker must not submit the draft. Return to US, then India: cached metadata keeps each country's own fetch time/results.
3. Using the temporary external Apple transport/clock runner described above, fail a submitted India search, edit the draft, then Retry. Observe the original failed phrase and `country=in`, not the draft. Return empty Indian results after populated US results and verify honest no-match with no confirmed app; fail an Indian request and verify its error context without US fallback.
4. Hold an older US response behind an event, switch to India, confirm a newer candidate, then release the old response before its eight-second deadline. Repeat with a changed phrase/country and an older failure. Newest identity/confirmation must remain; an invalid latest submission must also invalidate old work. Use events, not timing sleeps, and retain dispatch order evidence.
5. Reload: US, blank input, Keyword mode, no results/confirmation and no search parameters. Smoke Keyword/App name, local return, metadata/app-ID copy and per-country freshness together; check keyboard focus, accessible country/status labels, and 320/768/1024/1440px layouts.

For #19's two-tab scenario, use that same temporary runner with a representative Apple response held behind an event. Submit the same uncached phrase from two browser tabs before releasing it; observe one Apple dispatch and identical `fetchedAt`/results with `cached=false` for both. Repeat with a held Apple failure: both tabs must receive the structured error, and a manual retry after recovery must make a new dispatch and succeed. Do not replace the search service or add a fixture endpoint. The offline API suite proves TTL/budget timing without waiting a day or exhausting Apple's live service.

Implementation evidence and final acceptance/integration status are tracked on [#15](https://github.com/sanketsingh27/bibi/issues/15), [#16](https://github.com/sanketsingh27/bibi/issues/16), [#17](https://github.com/sanketsingh27/bibi/issues/17), [#18](https://github.com/sanketsingh27/bibi/issues/18), and [#19](https://github.com/sanketsingh27/bibi/issues/19). Live counts and catalog ordering change over time; an upstream failure or zero matches is not proof of the populated flow.
