import asyncio
from contextlib import asynccontextmanager

import httpx
import pytest

from bibi.main import create_app
from bibi.reviews import ReviewRecord, review_fingerprint


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


def saved_sample(app_id=42, country="us", *, text="Previously saved text", fetched_at="2026-10-20T10:00:00Z"):
    record = ReviewRecord(reviewId="saved-review", appId=app_id, country=country, title="Saved title",
                          text=text, stars=3, updatedAt="2026-10-20T10:00:00Z", version="1.0",
                          fetchedAt=fetched_at)
    return {
        "appId": app_id, "country": country, "reviews": [record.model_dump()],
        "fingerprint": review_fingerprint(app_id, country, [record]),
        "pageObservations": {"completedPages": [1], "pageGaps": [], "pagesAttempted": 1},
    }


async def collect(client, *, app_id=42, country="us", request_id="sample-1", target=200):
    started = await client.post(f"/api/v1/apps/{app_id}/review-fetches", json={
        "requestId": request_id, "country": country, "targetCount": target,
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
    ("42", {"requestId": "x", "country": "us", "targetCount": 1000}),
    ("42", {"requestId": "x", "country": "us", "targetCount": 200, "reviews": []}),
])
async def test_invalid_scope_or_body_never_dispatches(app_id, body):
    calls = []
    async with api(lambda request: calls.append(request) or feed([])) as client:
        response = await client.post(f"/api/v1/apps/{app_id}/review-fetches", json=body)
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []


@pytest.mark.parametrize("mutate", [
    lambda sample: sample.update(fingerprint="0" * 64),
    lambda sample: sample["pageObservations"].update(completedPages=[11]),
    lambda sample: sample["pageObservations"].update(pageGaps=[2]),
    lambda sample: sample["reviews"][0].update(stars=6),
    lambda sample: sample["reviews"][0].update(country="ca"),
])
async def test_browser_supplied_sample_fingerprint_and_pages_are_validated_before_dispatch(mutate):
    calls = []
    sample = saved_sample()
    mutate(sample)
    async with api(lambda request: calls.append(request) or feed([])) as client:
        response = await client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "untrusted-sample", "country": "us", "targetCount": 200,
            "existingSample": sample,
        })
    assert response.status_code == 422
    assert response.json()["error"]["code"] == "VALIDATION_ERROR"
    assert calls == []


async def test_sample_fingerprint_ignores_fetch_time_but_tracks_review_content():
    first = saved_sample(fetched_at="2026-10-20T10:00:00Z")
    refetched = saved_sample(fetched_at="2026-10-21T10:00:00Z")
    edited = saved_sample(text="Substantive edit")
    assert first["fingerprint"] == refetched["fingerprint"]
    assert first["fingerprint"] != edited["fingerprint"]


async def test_refresh_replaces_changed_review_text_without_inflating_unique_count():
    calls = []

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        return feed([review("saved-review", content={"label": "Updated source text"})] if page == 1 else [])

    async with api(apple) as client:
        started = await client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "refresh-existing", "country": "us", "targetCount": 200,
            "refresh": True, "existingSample": saved_sample(),
        })
        operation_id = started.json()["operationId"]
        for _ in range(100):
            await asyncio.sleep(0)
            operation = (await client.get(f"/api/v1/operations/{operation_id}")).json()
            if operation["status"] not in {"queued", "running"}:
                break

    assert operation["status"] == "succeeded"
    assert operation["result"]["count"] == 1
    assert operation["result"]["reviews"][0]["text"] == "Updated source text"
    assert calls == list(range(1, 11))


async def test_failed_refresh_returns_no_replacement_and_preserves_prior_browser_sample():
    original = saved_sample()
    snapshot = repr(original)
    async with api(lambda request: httpx.Response(503)) as client:
        operation = await collect_refresh(client, original)
    assert operation["status"] == "failed"
    assert operation["result"]["reviews"] == []
    assert repr(original) == snapshot


async def collect_refresh(client, sample):
    started = await client.post("/api/v1/apps/42/review-fetches", json={
        "requestId": "failed-refresh", "country": "us", "targetCount": 200,
        "refresh": True, "existingSample": sample,
    })
    operation_id = started.json()["operationId"]
    for _ in range(100):
        await asyncio.sleep(0)
        operation = (await client.get(f"/api/v1/operations/{operation_id}")).json()
        if operation["status"] not in {"queued", "running"}:
            return operation
    raise AssertionError("refresh operation did not finish")


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


async def test_explicit_500_target_stops_at_ten_pages():
    calls = []

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        return feed([review(f"page-{page}-{index}") for index in range(50)])

    async with api(apple) as client:
        operation = await collect(client, target=500)
    assert operation["status"] == "succeeded"
    assert operation["targetCount"] == 500
    assert operation["result"]["count"] == 500
    assert operation["result"]["targetReached"] is True
    assert calls == list(range(1, 11))


async def test_cancel_during_pacing_retains_records_and_resume_skips_successful_page():
    calls = []
    pacing = asyncio.Event()
    waiting = asyncio.Event()
    now = [0.0]

    async def sleeper(seconds):
        waiting.set()
        await pacing.wait()
        now[0] += seconds

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        return feed([review("first-page-review")] if page == 1 else [])

    async with api(apple, clock=lambda: now[0], sleeper=sleeper) as client:
        started = await client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "cancel-resume", "country": "us", "targetCount": 200,
        })
        operation_id = started.json()["operationId"]
        await asyncio.wait_for(waiting.wait(), timeout=1)
        cancelled = await client.post(f"/api/v1/operations/{operation_id}/cancel")
        for _ in range(20):
            cancelled = await client.get(f"/api/v1/operations/{operation_id}")
            if cancelled.json()["status"] == "cancelled":
                break
            await asyncio.sleep(0)
        assert cancelled.json()["status"] == "cancelled"
        assert cancelled.json()["result"]["count"] == 1
        assert calls == [1]
        pacing.set()
        resumed = await client.post(f"/api/v1/operations/{operation_id}/resume")
        for _ in range(100):
            await asyncio.sleep(0)
            current = await client.get(f"/api/v1/operations/{operation_id}")
            if current.json()["status"] not in {"queued", "running"}:
                break

    assert current.json()["status"] == "succeeded"
    assert current.json()["result"]["count"] == 1
    assert calls == list(range(1, 11))
    assert resumed.json()["operationId"] == operation_id


async def test_rate_limit_retry_after_pauses_without_retry_and_explicit_resume_keeps_partial_results():
    now = [0.0]
    calls = []

    async def advance(seconds):
        now[0] += seconds

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        if page == 2 and calls.count(2) == 1:
            return httpx.Response(429, headers={"Retry-After": "30"})
        return feed([review("kept-review")] if page == 1 else [])

    async with api(apple, clock=lambda: now[0], sleeper=advance) as client:
        started = await client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "rate-limit", "country": "us", "targetCount": 200,
        })
        operation_id = started.json()["operationId"]
        for _ in range(100):
            await asyncio.sleep(0)
            limited = await client.get(f"/api/v1/operations/{operation_id}")
            if limited.json()["status"] == "rate-limited":
                break
        assert limited.json()["status"] == "rate-limited"
        assert limited.json()["result"]["count"] == 1
        assert limited.json()["progress"]["pagesAttempted"] == 2
        assert limited.json()["resumeAt"] is not None
        assert calls == [1, 2]
        early = await client.post(f"/api/v1/operations/{operation_id}/resume")
        assert early.status_code == 429
        now[0] = 31
        await client.post(f"/api/v1/operations/{operation_id}/resume")
        for _ in range(100):
            await asyncio.sleep(0)
            complete = await client.get(f"/api/v1/operations/{operation_id}")
            if complete.json()["status"] not in {"queued", "running"}:
                break

    assert complete.json()["status"] == "succeeded"
    assert complete.json()["result"]["count"] == 1
    assert complete.json()["result"]["pagesAttempted"] == 11
    assert calls == [1, 2, 2, *range(3, 11)]


async def test_expanding_completed_200_sample_to_500_reuses_successful_pages():
    calls = []

    def apple(request):
        page = int(request.url.path.split("page=")[1].split("/")[0])
        calls.append(page)
        return feed([review(f"page-{page}-{index}") for index in range(50)])

    async with api(apple) as client:
        first = await collect(client, target=200)
        expanded = await client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "expanded", "country": "us", "targetCount": 500,
        })
        operation_id = expanded.json()["operationId"]
        for _ in range(100):
            await asyncio.sleep(0)
            result = await client.get(f"/api/v1/operations/{operation_id}")
            if result.json()["status"] not in {"queued", "running"}:
                break

    assert first["result"]["count"] == 200
    assert result.json()["status"] == "succeeded"
    assert result.json()["result"]["count"] == 500
    assert calls == list(range(1, 11))


async def test_unknown_operation_after_restart_is_reported_without_resubmission():
    calls = []
    async with api(lambda request: calls.append(request) or feed([])) as first_client:
        operation = await first_client.post("/api/v1/apps/42/review-fetches", json={
            "requestId": "lost", "country": "us", "targetCount": 200,
        })
        operation_id = operation.json()["operationId"]
        for _ in range(100):
            await asyncio.sleep(0)
            status = await first_client.get(f"/api/v1/operations/{operation_id}")
            if status.json()["status"] not in {"queued", "running"}:
                break
        dispatched_before_restart = len(calls)

    async with api(lambda request: calls.append(request) or feed([])) as restarted_client:
        response = await restarted_client.get(f"/api/v1/operations/{operation_id}")
    assert response.status_code == 404
    assert response.json()["error"]["code"] == "OPERATION_NOT_FOUND"
    assert "this process" in response.json()["error"]["message"]
    assert len(calls) == dispatched_before_restart


async def test_operation_controls_reject_cross_origin_requests():
    async with api(lambda request: feed([])) as client:
        unknown = await client.post("/api/v1/operations/missing/cancel", headers={"Origin": "https://evil.test"})
    assert unknown.status_code == 403
    assert unknown.json()["error"]["code"] == "LOCAL_REQUEST_FORBIDDEN"


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
