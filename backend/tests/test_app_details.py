import asyncio

import httpx
import pytest

from test_search import api, listing, payload


async def test_exact_lookup_uses_id_and_storefront_with_real_listing_header():
    calls = []
    def apple(request):
        calls.append(request)
        return payload([listing(42, trackName="Same name", artistName="Chosen developer",
                                trackViewUrl="https://apps.apple.com/ca/app/same/id42",
                                userRatingCount=0)])
    async with api(apple) as client:
        response = await client.get("/api/v1/apps/42", params={"country": "ca"})
        assert response.status_code == 200
        body = response.json()
        assert body["appId"] == 42 and body["country"] == "ca"
        assert body["name"] == "Same name" and body["developer"] == "Chosen developer"
        assert body["ratingCount"] == 0 and body["averageRating"] is None
        assert body["storeUrl"] == "https://apps.apple.com/ca/app/same/id42"
        assert body["cached"] is False and body["fetchedAt"].endswith("Z")
        assert response.headers["cache-control"] == "no-store"
    assert len(calls) == 1
    assert calls[0].url.path == "/lookup"
    assert dict(calls[0].url.params) == {"id": "42", "country": "ca", "entity": "software", "lang": "en_us"}


@pytest.mark.parametrize("app_id", ["0", "-1", "1.5", "true", "1e2", "9007199254740992", "+42", " 42", "４２"])
async def test_invalid_id_never_dispatches(app_id):
    calls = []
    async with api(lambda request: calls.append(request) or payload([])) as client:
        response = await client.get(f"/api/v1/apps/{app_id}", params={"country": "us"})
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []


@pytest.mark.parametrize("params", [{}, {"country": "zz"}, {"country": "US"}, {"country": " us "},
                                    {"country": ""}, {"country": "us", "q": "name"},
                                    [("country", "us"), ("country", "ca")]])
async def test_invalid_storefront_or_parameters_never_dispatch(params):
    calls = []
    async with api(lambda request: calls.append(request) or payload([])) as client:
        response = await client.get("/api/v1/apps/42", params=params)
    assert response.status_code == 422
    assert calls == []


@pytest.mark.parametrize("records", [[], [listing(43)], [listing(True)], [listing("42")],
                                    [listing(42, kind="song")], [listing(43), listing(42, kind="song")]])
async def test_wrong_or_missing_software_is_unavailable_without_substitution(records):
    async with api(lambda request: payload(records)) as client:
        response = await client.get("/api/v1/apps/42?country=us")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "APP_UNAVAILABLE"


async def test_exact_software_is_selected_even_after_unrelated_records_and_safe_integer_max():
    app_id = 9007199254740991
    async with api(lambda request: payload([listing(7), listing(app_id)])) as client:
        response = await client.get(f"/api/v1/apps/{app_id}?country=us")
    assert response.status_code == 200
    assert response.json()["appId"] == app_id


@pytest.mark.parametrize("url", ["javascript:alert(1)", "https://apps.apple.com.evil.test/us/app/id42",
                                 "https://apps.apple.com@evil.test/us/app/id42", "http://apps.apple.com/us/app/id42"])
async def test_unsafe_original_listing_link_is_withheld(url):
    async with api(lambda request: payload([listing(42, trackViewUrl=url)])) as client:
        response = await client.get("/api/v1/apps/42?country=us")
    assert response.status_code == 200
    assert response.json()["storeUrl"] is None


@pytest.mark.parametrize("body", ["null", "not json", '{"resultCount":1,"results":[]}',
                                 '{"resultCount":1,"results":[null]}'])
async def test_malformed_lookup_is_a_source_error(body):
    async with api(lambda request: httpx.Response(200, content=body)) as client:
        response = await client.get("/api/v1/apps/42?country=us")
    assert response.status_code == 502
    assert response.json()["error"]["code"] == "UPSTREAM_ERROR"


async def test_exact_cache_preserves_original_fetch_time_expires_and_isolates_storefronts():
    now = [0.0]
    calls = []
    def apple(request):
        calls.append(request)
        return payload([listing(int(request.url.params["id"]))])
    async with api(apple, clock=lambda: now[0]) as client:
        first = await client.get("/api/v1/apps/42?country=us")
        now[0] = 86399.999
        assert (await client.get("/api/v1/apps/42?country=us")).json() == {**first.json(), "cached": True}
        assert (await client.get("/api/v1/apps/42?country=ca")).json()["country"] == "ca"
        assert (await client.get("/api/v1/apps/43?country=us")).json()["appId"] == 43
        now[0] = 86400.0
        assert (await client.get("/api/v1/apps/42?country=us")).json()["cached"] is False
    assert len(calls) == 4


async def test_identical_lookup_callers_share_work_and_cache_the_original_snapshot():
    started, joined, release = asyncio.Event(), asyncio.Event(), asyncio.Event()
    calls, reads = [], [0]
    def clock():
        reads[0] += 1
        if reads[0] == 2:
            joined.set()
        return 0.0
    async def apple(request):
        calls.append(request)
        started.set()
        await release.wait()
        return payload([listing(42)])
    async with api(apple, clock=clock) as client:
        first = asyncio.create_task(client.get("/api/v1/apps/42?country=us"))
        await asyncio.wait_for(started.wait(), 2)
        second = asyncio.create_task(client.get("/api/v1/apps/42?country=us"))
        try:
            await asyncio.wait_for(joined.wait(), 2)
            assert len(calls) == 1
        finally:
            release.set()
            responses = await asyncio.gather(first, second)
        assert responses[0].status_code == responses[1].status_code == 200
        assert responses[0].json() == responses[1].json()
        assert (await client.get("/api/v1/apps/42?country=us")).json() == {**responses[0].json(), "cached": True}
    assert len(calls) == 1


async def test_lookup_and_search_share_rolling_budget_including_failed_attempts_and_static_routes():
    now, calls = [0.0], []
    def apple(request):
        calls.append(request)
        return httpx.Response(503)
    async with api(apple, clock=lambda: now[0]) as client:
        for index in range(5):
            assert (await client.get(f"/api/v1/apps/{index + 1}?country=us")).status_code == 502
            assert (await client.get("/api/v1/apps/search", params={"q": f"phrase {index}"})).status_code == 502
        limited = await client.get("/api/v1/apps/99?country=us")
        assert limited.status_code == 429 and limited.headers["retry-after"] == "60"
        assert limited.json()["error"]["code"] == "SEARCH_RATE_LIMITED"
        assert (await client.get("/api/v1/apps/storefronts")).status_code == 200
        now[0] = 60.0
        assert (await client.get("/api/v1/apps/99?country=us")).status_code == 502
    assert len(calls) == 11


@pytest.mark.parametrize("failure,status,code", [
    (httpx.ReadTimeout("private timeout"), 504, "UPSTREAM_TIMEOUT"),
    (httpx.ConnectError("private host"), 502, "UPSTREAM_ERROR"),
    (httpx.Response(429, headers={"Retry-After": "17"}), 429, "UPSTREAM_RATE_LIMITED"),
])
async def test_lookup_source_failures_are_safe_single_attempts_and_not_cached(failure, status, code):
    calls = []
    def apple(request):
        calls.append(request)
        if isinstance(failure, Exception):
            raise failure
        return failure
    async with api(apple) as client:
        for _ in range(2):
            response = await client.get("/api/v1/apps/42?country=us")
            assert response.status_code == status and response.json()["error"]["code"] == code
            assert "private" not in response.text
            if status == 429:
                assert response.headers["retry-after"] == "17"
    assert len(calls) == 2


async def test_lookup_overall_deadline_includes_blocked_body(monkeypatch):
    started = asyncio.Event()
    class BlockedBody(httpx.AsyncByteStream):
        async def __aiter__(self):
            started.set()
            await asyncio.Event().wait()
            yield b"never"
    loop = asyncio.get_running_loop()
    real_time, offset = loop.time, [0.0]
    async with api(lambda request: httpx.Response(200, stream=BlockedBody())) as client:
        with monkeypatch.context() as patch:
            patch.setattr(loop, "time", lambda: real_time() + offset[0])
            task = asyncio.create_task(client.get("/api/v1/apps/42?country=us"))
            await asyncio.wait_for(started.wait(), 2)
            offset[0] = 8.0
            response = await task
    assert response.status_code == 504
    assert response.json()["error"]["code"] == "UPSTREAM_TIMEOUT"


async def test_static_search_and_catalog_remain_available_without_ai_configuration():
    async with api(lambda request: payload([listing(42)])) as client:
        assert (await client.get("/api/v1/apps/storefronts")).json()["defaultCountry"] == "us"
        response = await client.get("/api/v1/apps/search?q=planner&country=us")
    assert response.status_code == 200
    assert response.json()["results"][0]["appId"] == 42


@pytest.mark.parametrize("optional", [{}, {
    "description": None, "screenshotUrls": None, "ipadScreenshotUrls": {},
    "version": 3, "formattedPrice": False, "releaseDate": "yesterday",
    "currentVersionReleaseDate": {}, "releaseNotes": [],
}])
async def test_optional_details_stay_unavailable_without_losing_legitimate_zero_ratings(optional):
    async with api(lambda request: payload([listing(42, averageUserRating=0, userRatingCount=0, **optional)])) as client:
        response = await client.get("/api/v1/apps/42?country=us")
    assert response.status_code == 200
    body = response.json()
    assert body["averageRating"] == 0 and body["ratingCount"] == 0
    for field in ("description", "version", "formattedPrice", "releaseDate", "currentVersionReleaseDate", "releaseNotes"):
        assert body[field] is None
    assert body["screenshotUrls"] == []


async def test_details_keep_text_inert_and_filter_unsafe_screenshots_without_hiding_listing():
    async with api(lambda request: payload([listing(42,
            description="<script>alert(1)</script>", releaseNotes="<img src=x onerror=alert(1)>",
            screenshotUrls=["javascript:alert(1)", "https://images.apple.com/one.png", None,
                            "https://user:pass@evil.test/a", "https://evil.test:444/a", "data:image/svg+xml,x"],
            ipadScreenshotUrls=["https://images.apple.com/one.png", "https://images.apple.com/two.png"],
            version="2.0", formattedPrice="$0.00", releaseDate="2024-01-01T00:00:00Z",
            currentVersionReleaseDate="2026-10-01T12:00:00Z")])) as client:
        response = await client.get("/api/v1/apps/42?country=us")
    assert response.status_code == 200
    body = response.json()
    assert body["screenshotUrls"] == ["https://images.apple.com/one.png", "https://images.apple.com/two.png"]
    assert body["description"].startswith("<script>") and body["releaseNotes"].startswith("<img")
    assert body["formattedPrice"] == "$0.00" and body["version"] == "2.0"
    assert body["releaseDate"].endswith("Z") and body["currentVersionReleaseDate"].endswith("Z")
