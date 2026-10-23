import asyncio
import math
from collections import deque
from collections.abc import Callable
from datetime import datetime, timezone
from email.utils import parsedate_to_datetime

import httpx

from .models import AppDetailsResponse, SearchResponse, normalize_results


SEARCH_PARAMETERS = (("media", "software"), ("entity", "software"), ("lang", "en_us"))
type SearchKey = tuple[str, str, int, tuple[tuple[str, str], ...]]
type LookupKey = tuple[int, str]
type MetadataResponse = SearchResponse | AppDetailsResponse


class SearchError(Exception):
    def __init__(self, status: int, code: str, message: str, retry_after: str | None = None):
        self.status = status
        self.code = code
        self.message = message
        self.retry_after = retry_after


def valid_retry_after(value: str | None) -> str | None:
    if value is None:
        return None
    if value.isascii() and value.isdecimal():
        return value
    try:
        parsed = parsedate_to_datetime(value)
        if parsed.tzinfo is not None:
            return value
    except (ValueError, TypeError, OverflowError):
        pass
    return None


class SearchService:
    def __init__(self, client: httpx.AsyncClient, clock: Callable[[], float]):
        self.client = client
        self.clock = clock
        self.dispatched: deque[float] = deque()
        self.cache: dict[SearchKey | LookupKey, tuple[float, MetadataResponse]] = {}
        self.pending: dict[SearchKey | LookupKey, asyncio.Task[MetadataResponse]] = {}

    async def search(self, query: str, country: str, limit: int) -> SearchResponse:
        key = (query, country, limit, SEARCH_PARAMETERS)
        return await self._load(key)

    async def lookup(self, app_id: int, country: str) -> AppDetailsResponse:
        return await self._load((app_id, country))

    async def _load(self, key: SearchKey | LookupKey) -> MetadataResponse:
        now = self.clock()
        entry = self.cache.get(key)
        if entry is not None:
            expires_at, response = entry
            if now < expires_at:
                return response.model_copy(update={"cached": True})
            del self.cache[key]
        task = self.pending.get(key)
        if task is not None:
            return await asyncio.shield(task)
        while self.dispatched and self.dispatched[0] <= now - 60:
            self.dispatched.popleft()
        if len(self.dispatched) >= 10:
            raise SearchError(429, "SEARCH_RATE_LIMITED", "Search budget reached. Retry after the indicated wait.",
                              str(max(1, math.ceil(self.dispatched[0] + 60 - now))))
        # No await between checking cache/pending/budget and reserving shared work:
        # atomic in this single-worker event loop. Failed attempts also consume a slot.
        self.dispatched.append(now)
        task = asyncio.create_task(self._fetch(key))
        self.pending[key] = task
        # A disconnected caller must not cancel work shared by other tabs.
        # Retrieve failures even if every waiter disconnects before completion.
        task.add_done_callback(lambda done: None if done.cancelled() else done.exception())
        return await asyncio.shield(task)

    async def aclose(self) -> None:
        tasks = list(self.pending.values())
        for task in tasks:
            task.cancel()
        await asyncio.gather(*tasks, return_exceptions=True)

    async def _fetch(self, key: SearchKey | LookupKey) -> MetadataResponse:
        try:
            response = await self._request(*key) if len(key) == 2 else await self._request(*key[:3])
            self.cache[key] = (self.clock() + 86400, response)
            return response
        finally:
            del self.pending[key]

    async def _request(self, query: str | int, country: str, limit: int | None = None) -> MetadataResponse:
        try:
            async with asyncio.timeout(8):
                params = {"id": query, "country": country, "entity": "software", "lang": "en_us"} if limit is None else {
                    "term": query, "country": country, "limit": limit,
                    **dict(SEARCH_PARAMETERS),
                }
                response = await self.client.get(
                    "https://itunes.apple.com/lookup" if limit is None else "https://itunes.apple.com/search", params=params)
                if response.status_code == 429:
                    raise SearchError(429, "UPSTREAM_RATE_LIMITED", "Apple is limiting searches. Retry manually later.",
                                      valid_retry_after(response.headers.get("retry-after")))
                if not response.is_success:
                    raise SearchError(502, "UPSTREAM_ERROR", "Apple search is unavailable. Retry manually.")
                envelope = response.json()
                if (not isinstance(envelope, dict) or type(envelope.get("resultCount")) is not int
                        or envelope["resultCount"] < 0 or not isinstance(envelope.get("results"), list)
                        or envelope["resultCount"] != len(envelope["results"])
                        or any(not isinstance(record, dict) for record in envelope["results"])):
                    raise ValueError("Malformed Apple envelope")
                records = envelope["results"]
                if limit is None:
                    records = [record for record in records if type(record.get("trackId")) is int and record["trackId"] == query]
                results = normalize_results(records, country, limit or 1)
        except (TimeoutError, httpx.TimeoutException) as error:
            raise SearchError(504, "UPSTREAM_TIMEOUT", "Apple search timed out. Retry manually.") from error
        except (httpx.HTTPError, ValueError, UnicodeError) as error:
            raise SearchError(502, "UPSTREAM_ERROR", "Apple search is unavailable. Retry manually.") from error
        fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
        if limit is None:
            if not results:
                raise SearchError(404, "APP_UNAVAILABLE", "This exact app is unavailable in the requested storefront.")
            return AppDetailsResponse(**results[0].model_dump(), fetchedAt=fetched_at, cached=False)
        return SearchResponse(query=query, country=country, fetchedAt=fetched_at, cached=False, results=results)
