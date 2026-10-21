# Bibi — local App Store discovery

Ticket [#15](https://github.com/sanketsingh27/bibi/issues/15), under [spec #14](https://github.com/sanketsingh27/bibi/issues/14), adds a separate local keyword-discovery application; [#17](https://github.com/sanketsingh27/bibi/issues/17) adds explicit App name mode and local confirmation. `landing-page/` remains the existing informational site, unchanged.

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

The API must remain running. These commands deliberately bind both applications to loopback. One backend worker/process is required: multiple workers or public hosting are unsupported because the request budget is process-local. Restarting the API clears that budget.

The frontend's `.npmrc` disables dependency lifecycle scripts. The locked install and Next.js build work with scripts disabled; do not blanket-enable installation scripts. `backend/uv.lock` and `frontend/package-lock.json` pin each independent installation boundary.

## Searching

The screen starts blank in **Keyword** mode in the United States storefront. Choose **Keyword** for a market phrase or **App name** for a known product, then use **Search** or **Enter**. Typing and focusing never search. Both modes use the same search endpoint with only `q`, `country`, and `limit`; mode is browser presentation, not inferred intent or an exact-title algorithm. Results retain Apple's returned order, show at most 50 matches, and are not a complete App Store catalog or a classified competitor set.

Each row identifies the name, developer, numeric Apple ID, and original safe listing link. Missing information is marked unavailable. Loading, no matches, invalid input, rate limits, timeout, and upstream failure have separate states. Manual Retry repeats the failed submitted phrase/storefront even if the input contains a newer draft. A newer submission invalidates older responses, including when the newer input is invalid.

In **App name** mode, compare candidate names and developers, then choose **Confirm app** on the intended listing. Even one candidate requires explicit confirmation; zero candidates remains no match. Confirmation shows only that listing. **Return to candidates** reuses the same fetched response without another request. Mode changes also make no request: they clear confirmation and expose the existing matches/candidates. New submissions (including invalid input) clear confirmation. Editing the draft alone leaves the submitted results and confirmation intact. Native radio controls, confirmation, and return are keyboard-operable; confirmation/return focus the result heading and announce status. Confirmation is not saved and triggers no review collection or research action.

The submitted query/storefront, limited-match count, metadata fetch time and cache status belong to the displayed response. This ticket has **no metadata cache**: each successful search truthfully returns `cached=false`, including repeated and empty searches. There are no automatic retries, background searches, polling, queues, fallback data, saved browser search state, or search phrases in the page URL. Reload starts fresh. Browser requests and responses are not used as another metadata cache.

The country-picker interaction, icon/category/ratings/copy UI, and metadata caching/request sharing belong to later tickets and are intentionally absent here. The API already supplies their complete normalized metadata contract and storefront catalog.

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

The single process reserves at most **10 dispatched attempts in a rolling 60 seconds**, including failures and simultaneous requests. It rejects excess work immediately before dispatch. Every Apple operation has an **8-second overall deadline**, including reading the body, with TLS verification and no automatic retries or redirect following. Identical searches do not share an attempt in this ticket.

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

From `backend/`, with `.venv` activated, `python -m pytest` runs the offline behavioral API suite. It uses the real FastAPI boundary/service and controls only the Apple HTTPX transport and time. Tests cover input/catalog agreement, ordering/filtering/deduplication/capping, nullable metadata and safe URLs, empty versus malformed results, failures/429/timeout, failed-attempt accounting, exact rolling-window boundaries, concurrent reservations, and the overall deadline during a blocked body read. There is no separate helper/UI unit-test seam.

From `frontend/`, run `npm run build` and `npm audit`. From the repository root, with both servers running:

```sh
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/search?q=adhd%20planner&country=us&limit=50'
curl --fail-with-body 'http://127.0.0.1:8000/api/v1/apps/storefronts'
```

Browser runtime acceptance is separate from the suite/build:

1. Open the blank US-scoped screen. Focus/type `adhd planner` and confirm no search request in browser Network. Submit using Search, then submit another phrase using Enter. Observe actual populated Apple results, not a fixed expected count.
2. Open an original listing; verify navigation to Apple's listing and no review/research work. Check the limited-match count, submitted phrase/storefront and fresh/not-cached timestamp. Repeat a search; it must make another attempt, subject to the budget.
3. Submit rapidly changing phrases. Older responses must not overwrite the newer submission. Reload and confirm blank input, no result rows, US context and no page search parameters.
4. For deterministic failures, wrap the real `create_app(apple_transport=..., clock=...)` in a **temporary local-only runner** using `httpx.MockTransport`, as the API tests do. Start that runner on port 8000 instead of the live backend, leaving the real Next.js path unchanged. Exercise successful empty, invalid query, Apple 429 with/without Retry-After, 503, and a blocked operation hitting the real 8-second deadline. Do not add fixture endpoints or fallbacks to the application.
5. In that controlled runner, hold an older response behind an event, complete a newer search, then release the old response. Fail a submitted phrase, edit the draft, and use Retry: the request must still contain the failed phrase. Admit ten controlled dispatches (including failures), observe the next local 429 without an eleventh Apple dispatch, advance the controlled clock and retry manually. Inspect network/dispatch logs for no automatic retries. Check keyboard operation and 320/768/1024/1440px layouts.

For [#17](https://github.com/sanketsingh27/bibi/issues/17), use this additional browser scenario (no separate UI/helper test suite):

1. Keyboard-select **App name**, type `Tiimo` without submitting, and verify zero search traffic. Submit with Enter; compare the populated candidate names/developers and confirm the intended app. Verify only that listing appears.
2. Keyboard-activate **Return to candidates** and verify no additional search request. Confirm again, switch to Keyword and back, and verify the same fetched set is exposed without a request or retained confirmation.
3. Confirm a candidate, edit the draft, and verify the submitted identity/selection is unchanged. Submit another phrase and verify confirmation clears. Repeat with invalid input. Reload and verify blank input, Keyword mode, and no selection.
4. Through the temporary controlled Apple transport runner described above, return exactly one candidate and then zero candidates. Verify the single result still requires confirmation and the empty set has no confirmation/return action or substituted product. With two candidates, confirm the second to rule out implicit first-result selection.
5. Hold an older response behind an event, submit a newer phrase, and release the older response before its deadline. The newer result/confirmation must remain. Inspect browser requests for only `q`, `country`, `limit` and no mode, Lookup/review/AI calls, automatic retries, or confirmation requests. Check accessible labels, keyboard actions and responsive layouts.

Observed implementation evidence and final acceptance/integration status are recorded on [#15](https://github.com/sanketsingh27/bibi/issues/15) and [#17](https://github.com/sanketsingh27/bibi/issues/17). Live counts and catalog ordering change over time; an upstream failure or zero matches is not proof of the populated flow.
