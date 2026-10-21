import asyncio
from contextlib import asynccontextmanager
from datetime import datetime

import httpx
import pytest

from bibi.main import create_app


@asynccontextmanager
async def api(handler, clock=lambda: 0.0):
    app = create_app(apple_transport=httpx.MockTransport(handler), clock=clock)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(
            transport=httpx.ASGITransport(app=app), base_url="http://bibi.test"
        ) as client:
            yield client


def listing(app_id, **fields):
    return {"kind": "software", "trackId": app_id, **fields}


def payload(records):
    return httpx.Response(200, json={"resultCount": len(records), "results": records})


@pytest.mark.parametrize("phrase", ["ab", "x" * 100, "  adhd\t planner\n"])
async def test_normalized_query_boundaries(phrase):
    async with api(lambda request: payload([])) as client:
        response = await client.get("/api/v1/apps/search", params={"q": phrase})
    assert response.status_code == 200
    body = response.json()
    assert body["query"] == " ".join(phrase.split())
    assert body["country"] == "us"
    assert body["cached"] is False
    assert body["results"] == []
    assert datetime.fromisoformat(body["fetchedAt"].replace("Z", "+00:00")).utcoffset().total_seconds() == 0
    assert response.headers["cache-control"] == "no-store"


@pytest.mark.parametrize("params", [
    {}, {"q": ""}, {"q": " \t "}, {"q": "x"}, {"q": "x" * 101},
    {"q": "ab", "country": "zz"}, {"q": "ab", "country": ""},
    {"q": "ab", "limit": "0"}, {"q": "ab", "limit": "51"},
    {"q": "ab", "limit": "1.5"}, {"q": "ab", "limit": "true"},
    {"q": "ab", "offset": "1"}, [("q", "ab"), ("q", "cd")],
])
async def test_invalid_inputs_never_dispatch(params):
    calls = []
    def apple(request):
        calls.append(request)
        return payload([])
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/search", params=params)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []
    assert response.headers["cache-control"] == "no-store"


async def test_catalog_and_validation_share_supported_countries_without_fallback():
    calls = []
    def apple(request):
        calls.append(request)
        return payload([listing(1, trackName=request.url.params["country"])])
    async with api(apple) as client:
        catalog = (await client.get("/api/v1/apps/storefronts")).json()
        assert calls == []
        assert catalog["defaultCountry"] == "us"
        countries = {item["code"]: item["name"] for item in catalog["storefronts"]}
        assert countries["us"] == "United States"
        assert countries["in"] == "India"
        for country in countries:
            # Fresh process state per request: this checks the entire static allowlist,
            # not a rate-limit accident after its tenth entry.
            async with api(apple) as fresh:
                response = await fresh.get("/api/v1/apps/search", params={"q": "ab", "country": f" {country.upper()} "})
            assert response.status_code == 200
            assert response.json()["country"] == country
            assert response.json()["results"][0]["name"] == country
        assert (await client.get("/api/v1/apps/search", params={"q": "ab", "country": "aq"})).status_code == 422


async def test_software_search_is_country_scoped_ordered_deduplicated_and_capped():
    def apple(request):
        params = request.url.params
        if (request.url.host != "itunes.apple.com" or request.url.path != "/search"
                or params.get("media") != "software" or params.get("entity") != "software"
                or params.get("lang") != "en_us" or params.get("term") != "adhd planner"):
            return httpx.Response(400)
        return payload([
            listing(False), listing("3"), listing(-1), listing(2**53),
            {"kind": "song", "trackId": 3}, {"trackId": 3},
            listing(3, trackName="first usable"), listing(3, trackName="duplicate"),
            listing(2, trackName=params["country"]), listing(4),
        ])
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/search", params={"q": " adhd   planner ", "country": " IN ", "limit": 2})
        single = await client.get("/api/v1/apps/search", params={"q": "adhd planner", "limit": 1})
    assert response.status_code == 200
    rows = response.json()["results"]
    assert [row["appId"] for row in rows] == [3, 2]
    assert [row["name"] for row in rows] == ["first usable", "in"]
    assert all(row["country"] == "in" for row in rows)
    assert [row["appId"] for row in single.json()["results"]] == [3]


async def test_missing_invalid_optional_data_is_unavailable_not_fabricated():
    records = [
        listing(1),
        listing(2, trackName={"html": "bad"}, artistName=42, primaryGenreName=[],
                averageUserRating=True, userRatingCount=False,
                artworkUrl100="javascript:alert(1)", artworkUrl60="https://is1-ssl.mzstatic.com/a.jpg",
                trackViewUrl="https://apps.apple.com.evil.test/app/id2"),
        listing(3, trackName="<script>alert(1)</script>", averageUserRating=0, userRatingCount=0,
                trackViewUrl="https://apps.apple.com/us/app/example/id3"),
        listing(4, averageUserRating=5.1, userRatingCount=-1),
    ]
    async with api(lambda request: payload(records)) as client:
        rows = (await client.get("/api/v1/apps/search", params={"q": "ab"})).json()["results"]
    assert rows[0] == {"appId": 1, "name": None, "developer": None, "iconUrl": None,
                       "averageRating": None, "ratingCount": None, "category": None,
                       "storeUrl": None, "country": "us"}
    assert rows[1]["name"] is None and rows[1]["developer"] is None and rows[1]["category"] is None
    assert rows[1]["averageRating"] is None and rows[1]["ratingCount"] is None
    assert rows[1]["storeUrl"] is None
    assert rows[1]["iconUrl"] == "https://is1-ssl.mzstatic.com/a.jpg"
    assert rows[2]["name"] == "<script>alert(1)</script>"  # Text, never interpreted HTML.
    assert rows[2]["averageRating"] == 0 and rows[2]["ratingCount"] == 0
    assert rows[3]["averageRating"] is None and rows[3]["ratingCount"] is None


@pytest.mark.parametrize("url", [
    "http://apps.apple.com/us/app/id1", "javascript:alert(1)", "//apps.apple.com/app/id1",
    "https://apps.apple.com@evil.test/app/id1", "https://user@apps.apple.com/app/id1",
    "https://apps.apple.com:bad/app/id1", "https://apps.apple.com\\@evil.test/app/id1",
    "https://apps.apple.com/app/\nfoo", "https://example.com/app/id1", "https:///missing",
])
async def test_unsafe_or_malformed_listing_urls_never_become_links(url):
    async with api(lambda request: payload([listing(1, trackViewUrl=url)])) as client:
        row = (await client.get("/api/v1/apps/search", params={"q": "ab"})).json()["results"][0]
    assert row["storeUrl"] is None


@pytest.mark.parametrize("optional", [None, "4.8", True, -1, 6, {}, float("inf"), float("nan"), 10**400])
async def test_invalid_ratings_do_not_break_search(optional):
    import json
    def apple(request):
        return httpx.Response(200, content=json.dumps({"resultCount": 1, "results": [listing(1, averageUserRating=optional)]}))
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/search", params={"q": "ab"})
    assert response.status_code == 200
    assert response.json()["results"][0]["averageRating"] is None


@pytest.mark.parametrize("body", [
    "not json", "null", "[]", '{}', '{"resultCount":0}',
    '{"resultCount":0,"results":null}', '{"resultCount":"0","results":[]}',
    '{"resultCount":true,"results":[]}', '{"resultCount":-1,"results":[]}',
    '{"resultCount":1,"results":[]}', '{"resultCount":1,"results":[null]}',
])
async def test_malformed_envelopes_are_failures_not_empty_success(body):
    async with api(lambda request: httpx.Response(200, content=body)) as client:
        response = await client.get("/api/v1/apps/search", params={"q": "ab"})
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "UPSTREAM_ERROR"
    assert "results" not in response.json()


@pytest.mark.parametrize("status,code", [(403, "UPSTREAM_ERROR"), (500, "UPSTREAM_ERROR"), (302, "UPSTREAM_ERROR"), (429, "UPSTREAM_RATE_LIMITED")])
async def test_upstream_failure_never_retries_or_leaks_body(status, code):
    calls = []
    def apple(request):
        calls.append(request)
        return httpx.Response(status, text="private upstream failure details")
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/search", params={"q": "ab"})
    assert response.status_code == (429 if status == 429 else 502)
    assert response.json()["error"]["code"] == code
    assert "private upstream" not in response.text
    assert "retry-after" not in response.headers
    assert len(calls) == 1


@pytest.mark.parametrize("header,expected", [("12", "12"), ("Wed, 21 Oct 2099 07:28:00 GMT", "Wed, 21 Oct 2099 07:28:00 GMT"), ("-1", None), ("1.5", None), ("tomorrow", None), (None, None)])
async def test_apple_retry_after_preserves_only_valid_indications(header, expected):
    async with api(lambda request: httpx.Response(429, headers={} if header is None else {"Retry-After": header})) as client:
        response = await client.get("/api/v1/apps/search", params={"q": "ab"})
    assert response.status_code == 429
    assert response.headers.get("retry-after") == expected


@pytest.mark.parametrize("failure,code,status", [
    (httpx.ConnectError("private host details"), "UPSTREAM_ERROR", 502),
    (httpx.ReadTimeout("private deadline details"), "UPSTREAM_TIMEOUT", 504),
])
async def test_network_errors_and_timeouts_are_safe_single_attempts(failure, code, status):
    calls = []
    def apple(request):
        calls.append(request)
        raise failure
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/search", params={"q": "ab"})
    assert response.status_code == status
    assert response.json()["error"]["code"] == code
    assert "private" not in response.text
    assert len(calls) == 1


async def test_rolling_budget_counts_failures_rejects_before_dispatch_and_reopens_exactly():
    now = [0.0]
    calls = []
    def apple(request):
        calls.append(now[0])
        return httpx.Response(500) if len(calls) % 2 else payload([])
    async with api(apple, clock=lambda: now[0]) as client:
        for index in range(10):
            now[0] = float(index)
            response = await client.get("/api/v1/apps/search", params={"q": f"search {index}"})
            assert response.status_code in (200, 502)
        limited = await client.get("/api/v1/apps/search", params={"q": "overflow"})
        assert limited.status_code == 429
        assert limited.json()["error"]["code"] == "SEARCH_RATE_LIMITED"
        assert limited.headers["retry-after"] == "51"
        assert len(calls) == 10
        assert (await client.get("/api/v1/apps/storefronts")).status_code == 200
        now[0] = 59.1
        assert (await client.get("/api/v1/apps/search", params={"q": "early"})).headers["retry-after"] == "1"
        now[0] = 60.0
        assert (await client.get("/api/v1/apps/search", params={"q": "eligible"})).status_code == 502
        assert len(calls) == 11
        assert (await client.get("/api/v1/apps/search", params={"q": "still full"})).status_code == 429


async def test_concurrent_dispatches_reserve_slots_before_waiting_for_apple():
    entered = asyncio.Event()
    release = asyncio.Event()
    calls = []
    async def apple(request):
        calls.append(request)
        if len(calls) == 10:
            entered.set()
        await release.wait()
        return payload([])
    async with api(apple) as client:
        tasks = [asyncio.create_task(client.get("/api/v1/apps/search", params={"q": "same phrase"})) for _ in range(10)]
        try:
            await asyncio.wait_for(entered.wait(), 2)
            rejected = await client.get("/api/v1/apps/search", params={"q": "overflow"})
            assert rejected.status_code == 429
            assert len(calls) == 10
        finally:
            release.set()
            responses = await asyncio.gather(*tasks)
        assert all(response.status_code == 200 for response in responses)


async def test_overall_eight_second_deadline_includes_response_body(monkeypatch):
    started = asyncio.Event()
    calls = []
    class BlockedBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            started.set()
            await asyncio.Event().wait()
            yield b"never"
    def apple(request):
        calls.append(request)
        return httpx.Response(200, stream=BlockedBody())
    loop = asyncio.get_running_loop()
    real_time = loop.time
    offset = [0.0]
    async with api(apple) as client:
        with monkeypatch.context() as patch:
            patch.setattr(loop, "time", lambda: real_time() + offset[0])
            task = asyncio.create_task(client.get("/api/v1/apps/search", params={"q": "blocked body"}))
            await started.wait()
            offset[0] = 8.0
            response = await task
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "UPSTREAM_TIMEOUT"
    assert len(calls) == 1
