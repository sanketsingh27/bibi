import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest

from bibi.main import create_app


@asynccontextmanager
async def api(handler, clock=None, sleeper=None):
    if clock is None:
        now = [0.0]

        async def advance(seconds):
            now[0] += seconds

        clock = lambda: now[0]
        sleeper = sleeper or advance
    else:
        sleeper = sleeper or asyncio.sleep
    app = create_app(apple_transport=httpx.MockTransport(handler), clock=clock, sleeper=sleeper)
    async with app.router.lifespan_context(app):
        async with httpx.AsyncClient(transport=httpx.ASGITransport(app=app), base_url="http://127.0.0.1") as client:
            yield client


def review(review_id, **fields):
    return {
        "id": {"label": review_id}, "title": {"label": "A useful app"},
        "content": {"label": "The reminder feature works well."}, "im:rating": {"label": "4"},
        "updated": {"label": "2026-10-20T10:00:00Z"}, "im:version": {"label": "2.1"},
        "author": {"name": {"label": "Private reviewer"}, "uri": {"label": "https://example.test/profile"}},
        **fields,
    }


def feed(entries=None):
    value = {"feed": {}}
    if entries is not None:
        value["feed"]["entry"] = entries
    return httpx.Response(200, json=value)


async def collect(client, *, app_id=42, country="us", request_id="sample-1"):
    started = await client.post(f"/api/v1/apps/{app_id}/review-fetches", json={
        "requestId": request_id, "country": country, "targetCount": 200,
    })
    assert started.status_code == 202
    operation = started.json()
    for _ in range(100):
        await asyncio.sleep(0)
        response = await client.get(f"/api/v1/operations/{operation['operationId']}")
        operation = response.json()
        if operation["status"] not in {"queued", "running"}:
            return operation
    raise AssertionError("review operation did not finish")


async def test_collection_continues_after_empty_pages_and_accepts_a_single_entry():
    calls = []

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append((request.url.host, request.url.path))
        if page == 1:
            return feed([review("review-1")])
        if page == 4:
            return feed(review("review-4"))
        return feed([])

    now = [0.0]

    async def advance(seconds):
        now[0] += seconds

    async with api(apple, clock=lambda: now[0], sleeper=advance) as client:
        operation = await collect(client)

    assert operation["status"] == "succeeded"
    result = operation["result"]
    assert result["count"] == 2 and result["sourceAvailability"] == "available"
    assert result["pagesAttempted"] == 10
    assert result["pageGaps"] == [2, 3, 5, 6, 7, 8, 9, 10]
    assert [path.split("page=")[1].split("/")[0] for _, path in calls] == [str(i) for i in range(1, 11)]
    assert all(host == "itunes.apple.com" and path.startswith("/us/rss/customerreviews/page=") for host, path in calls)
    record = result["reviews"][1]
    assert record["reviewId"] == "review-4" and record["appId"] == 42 and record["country"] == "us"
    assert record["stars"] == 4 and record["text"] == "The reminder feature works well."
    assert "author" not in record and "profile" not in record


async def test_deduplicates_ids_and_warns_while_excluding_malformed_written_reviews():
    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        if page == 1:
            return feed([review("duplicate")])
        if page == 2:
            return feed([
                review("duplicate", content={"label": "Different duplicate"}),
                review("bad-stars", **{"im:rating": {"label": "6"}}),
                review("bad-text", content={"label": "  "}),
                review("bad-id", id={"label": "  "}),
                {"id": {"label": "app metadata"}, "im:name": {"label": "Example"}},
            ])
        return feed([])

    async with api(apple) as client:
        operation = await collect(client)
    result = operation["result"]
    assert result["count"] == 1
    assert result["reviews"][0]["text"] == "The reminder feature works well."
    assert result["warnings"] == ["Page 2: excluded 3 malformed written review record(s)."]


async def test_collection_stops_at_200_records_and_does_not_request_page_eleven():
    calls = []

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        return feed([review(f"page-{page}-{index}") for index in range(50)])

    now = [0.0]

    async def advance(seconds):
        now[0] += seconds

    async with api(apple, clock=lambda: now[0], sleeper=advance) as client:
        operation = await collect(client)
    assert operation["result"]["count"] == 200
    assert operation["result"]["targetReached"] is True
    assert calls == [1, 2, 3, 4]


async def test_empty_feed_is_successful_but_malformed_envelope_is_unavailable():
    now = [0.0]

    async def advance(seconds):
        now[0] += seconds

    async with api(lambda request: feed([]), clock=lambda: now[0], sleeper=advance) as client:
        empty = await collect(client)
        assert empty["status"] == "succeeded"
        assert empty["result"]["sourceAvailability"] == "empty"
        assert empty["result"]["count"] == 0

    async with api(lambda request: httpx.Response(200, json={"feed": []})) as client:
        failed = await collect(client, request_id="bad-feed")
    assert failed["status"] == "failed"
    assert failed["error"]["code"] == "UPSTREAM_ERROR"
    assert failed["result"]["sourceAvailability"] == "unavailable"


@pytest.mark.parametrize("app_id, body", [
    ("0", {"requestId": "x", "country": "us", "targetCount": 200}),
    ("42", {"requestId": "x", "country": "US", "targetCount": 200}),
    ("42", {"requestId": "x", "country": "us", "targetCount": 500}),
    ("42", {"requestId": "x", "country": "us", "targetCount": 200, "reviews": []}),
])
async def test_invalid_scope_or_body_never_dispatches(app_id, body):
    calls = []
    async with api(lambda request: calls.append(request) or feed([])) as client:
        response = await client.post(f"/api/v1/apps/{app_id}/review-fetches", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []


async def test_cross_origin_review_collection_is_rejected_before_dispatch():
    calls = []
    async with api(lambda request: calls.append(request) or feed([])) as client:
        response = await client.post("/api/v1/apps/42/review-fetches", headers={"Origin": "https://evil.test"}, json={
            "requestId": "cross-origin", "country": "us", "targetCount": 200,
        })
    assert response.status_code == 403
    assert response.json()["error"]["code"] == "LOCAL_REQUEST_FORBIDDEN"
    assert calls == []


async def test_request_id_replays_same_operation_and_rejects_changed_payload():
    held = asyncio.Event()

    async def apple(request):
        await held.wait()
        return feed([])

    async with api(apple) as client:
        first = await client.post("/api/v1/apps/42/review-fetches", json={"requestId": "same", "country": "us", "targetCount": 200})
        again = await client.post("/api/v1/apps/42/review-fetches", json={"requestId": "same", "country": "us", "targetCount": 200})
        changed = await client.post("/api/v1/apps/42/review-fetches", json={"requestId": "same", "country": "ca", "targetCount": 200})
        held.set()
        assert first.json()["operationId"] == again.json()["operationId"]
        assert changed.status_code == 409
        assert changed.json()["error"]["code"] == "OPERATION_CONFLICT"


async def test_app_and_storefront_reviews_remain_in_separate_scopes():
    now = [0.0]
    calls = []

    async def advance(seconds):
        now[0] += seconds

    def apple(request):
        country = request.url.path.split("/")[1]
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append((country, page))
        return feed([review("shared-source-id")] if page == 1 else [])

    async with api(apple, clock=lambda: now[0], sleeper=advance) as client:
        us = await client.post("/api/v1/apps/42/review-fetches", json={"requestId": "us", "country": "us", "targetCount": 200})
        ca = await client.post("/api/v1/apps/43/review-fetches", json={"requestId": "ca", "country": "ca", "targetCount": 200})
        assert us.json()["operationId"] != ca.json()["operationId"]
        operations = []
        for response in (us, ca):
            operation_id = response.json()["operationId"]
            operation = None
            for _ in range(100):
                await asyncio.sleep(0)
                operation = (await client.get(f"/api/v1/operations/{operation_id}")).json()
                if operation["status"] not in {"queued", "running"}:
                    break
            assert operation is not None and operation["status"] == "succeeded"
            operations.append(operation)

    first, second = [item["result"] for item in operations]
    assert (first["appId"], first["country"]) == (42, "us")
    assert (second["appId"], second["country"]) == (43, "ca")
    assert (first["reviews"][0]["appId"], first["reviews"][0]["country"]) == (42, "us")
    assert (second["reviews"][0]["appId"], second["reviews"][0]["country"]) == (43, "ca")
    assert {country for country, _ in calls} == {"us", "ca"}


async def test_review_pages_share_the_rolling_apple_dispatch_budget():
    now = [0.0]
    review_pages = []

    async def advance(seconds):
        now[0] += seconds

    def apple(request):
        if request.url.path == "/lookup":
            app_id = int(request.url.params["id"])
            return httpx.Response(200, json={"resultCount": 1, "results": [{"kind": "software", "trackId": app_id}]})
        page = int(request.url.path.split("page=")[1].split("/")[0])
        review_pages.append(page)
        return feed([])

    async with api(apple, clock=lambda: now[0], sleeper=advance) as client:
        for app_id in range(1, 10):
            assert (await client.get(f"/api/v1/apps/{app_id}?country=us")).status_code == 200
        operation = await collect(client)
    assert operation["status"] == "succeeded"
    assert review_pages == list(range(1, 11))
    assert now[0] >= 60
