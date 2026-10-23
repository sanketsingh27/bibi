import asyncio
import secrets
from collections.abc import Callable
from datetime import datetime, timezone

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .search import SearchError, SearchService
from .storefronts import STOREFRONTS


class ReviewFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requestId: str = Field(min_length=1, max_length=128)
    country: str
    targetCount: int = Field(ge=200, le=200)


class ReviewRecord(BaseModel):
    reviewId: str
    appId: int
    country: str
    title: str | None
    text: str
    stars: int
    updatedAt: str
    version: str | None
    fetchedAt: str


def _label(value: object) -> str | None:
    if isinstance(value, dict):
        value = value.get("label")
    return value.strip() if isinstance(value, str) and value.strip() else None


def _normalize_entry(entry: dict, app_id: int, country: str, fetched_at: str) -> ReviewRecord | None:
    # The feed's first entry can describe the app itself, not a written review.
    if "im:rating" not in entry and "content" not in entry:
        return None
    review_id = _label(entry.get("id"))
    text = _label(entry.get("content"))
    stars_text = _label(entry.get("im:rating"))
    updated_at = _label(entry.get("updated"))
    try:
        stars = int(stars_text) if stars_text and stars_text.isascii() and stars_text.isdecimal() else 0
        parsed = datetime.fromisoformat(updated_at.replace("Z", "+00:00")) if updated_at else None
    except ValueError:
        return None
    if (not review_id or len(review_id) > 256 or not text or len(text) > 100_000
            or not 1 <= stars <= 5 or parsed is None or parsed.tzinfo is None):
        return None
    return ReviewRecord(reviewId=review_id, appId=app_id, country=country,
                        title=_label(entry.get("title")), text=text, stars=stars,
                        updatedAt=updated_at, version=_label(entry.get("im:version")), fetchedAt=fetched_at)


class ReviewFetcher:
    def __init__(self, client: httpx.AsyncClient, search: SearchService):
        self.client = client
        self.search = search

    async def collect(self, app_id: int, country: str, operation: dict) -> None:
        records: list[dict] = []
        seen: set[str] = set()
        empty_pages: list[int] = []
        warnings: list[str] = []
        failed = False
        for page in range(1, 11):
            if len(records) >= operation["targetCount"]:
                break
            operation["progress"].update(currentPage=page)
            await self.search.reserve_review_dispatch()
            fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
            url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
            try:
                async with asyncio.timeout(8):
                    response = await self.client.get(url)
                if response.status_code == 429:
                    operation["error"] = {"code": "UPSTREAM_RATE_LIMITED",
                                           "message": "Apple is limiting review requests. No automatic retry was made."}
                    failed = True
                    break
                if not response.is_success:
                    raise ValueError("Apple review feed returned an unsuccessful response")
                envelope = response.json()
                feed = envelope.get("feed") if isinstance(envelope, dict) else None
                if not isinstance(feed, dict):
                    raise ValueError("Malformed Apple review feed")
                entries = feed.get("entry", [])
                if isinstance(entries, dict):
                    entries = [entries]
                if not isinstance(entries, list) or any(not isinstance(entry, dict) for entry in entries):
                    raise ValueError("Malformed Apple review entries")
            except (TimeoutError, httpx.TimeoutException):
                operation["error"] = {"code": "UPSTREAM_TIMEOUT", "message": "Apple review request timed out."}
                failed = True
                break
            except (httpx.HTTPError, ValueError, UnicodeError):
                operation["error"] = {"code": "UPSTREAM_ERROR", "message": "Apple's review feed is unavailable or malformed."}
                failed = True
                break

            page_records = 0
            invalid_records = 0
            for entry in entries:
                review = _normalize_entry(entry, app_id, country, fetched_at)
                if review is None:
                    if "im:rating" in entry or "content" in entry:
                        invalid_records += 1
                    continue
                if review.reviewId in seen:
                    continue
                seen.add(review.reviewId)
                records.append(review.model_dump())
                page_records += 1
                if len(records) >= operation["targetCount"]:
                    break
            if invalid_records:
                warnings.append(f"Page {page}: excluded {invalid_records} malformed written review record(s).")
            if page_records == 0:
                empty_pages.append(page)
            operation["progress"].update(count=len(records), pagesAttempted=page,
                                          pageGaps=empty_pages.copy())

        operation["result"] = {
            "appId": app_id, "country": country, "targetCount": operation["targetCount"],
            "count": len(records), "targetReached": len(records) >= operation["targetCount"],
            "reviews": records, "pagesAttempted": operation["progress"]["pagesAttempted"],
            "pageGaps": empty_pages, "warnings": warnings,
            "sourceAvailability": "available" if records and not failed else
                                 "partial" if records else "unavailable" if failed else "empty",
        }
        operation["progress"].update(currentPage=None, count=len(records), pageGaps=empty_pages.copy())
        if failed:
            operation["status"] = "partial" if records else "failed"
        else:
            operation["status"] = "succeeded"


class ReviewOperationManager:
    def __init__(self, fetcher: ReviewFetcher, clock: Callable[[], float]):
        self.fetcher = fetcher
        self.clock = clock
        self.operations: dict[str, dict] = {}
        self.requests: dict[str, tuple[tuple[int, str, int], str]] = {}
        self.scopes: dict[tuple[int, str], str] = {}
        self.tasks: set[asyncio.Task] = set()

    def _prune(self) -> None:
        now = self.clock()
        expired = [key for key, value in self.operations.items()
                   if value["status"] not in {"queued", "running"} and now - value["createdAt"] > 3600]
        for operation_id in expired:
            operation = self.operations.pop(operation_id)
            scope = (operation["scope"]["appId"], operation["scope"]["country"])
            if self.scopes.get(scope) == operation_id:
                del self.scopes[scope]
            self.requests = {request_id: value for request_id, value in self.requests.items()
                             if value[1] != operation_id}

    def start(self, app_id: int, request: ReviewFetchInput) -> dict:
        self._prune()
        if request.country not in STOREFRONTS:
            raise SearchError(422, "VALIDATION_ERROR", "Unsupported App Store storefront.")
        payload = (app_id, request.country, request.targetCount)
        prior = self.requests.get(request.requestId)
        if prior:
            if prior[0] != payload:
                raise SearchError(409, "OPERATION_CONFLICT", "This request ID is already associated with a different collection.")
            return self.get(prior[1])
        existing_id = self.scopes.get((app_id, request.country))
        if existing_id:
            existing = self.operations.get(existing_id)
            if existing and existing["status"] in {"queued", "running", "succeeded", "partial"}:
                self.requests[request.requestId] = (payload, existing_id)
                return self.get(existing_id)
        if sum(operation["status"] in {"queued", "running"} for operation in self.operations.values()) >= 2:
            raise SearchError(429, "SEARCH_RATE_LIMITED", "Two review collections are already active. Retry manually later.")

        operation_id = secrets.token_urlsafe(24)
        operation = {
            "operationId": operation_id, "kind": "review-fetch", "status": "queued",
            "scope": {"appId": app_id, "country": request.country}, "targetCount": request.targetCount,
            "progress": {"count": 0, "targetCount": request.targetCount,
                         "pagesAttempted": 0, "currentPage": None, "pageGaps": []},
            "result": None, "error": None, "createdAt": self.clock(),
        }
        self.operations[operation_id] = operation
        self.requests[request.requestId] = (payload, operation_id)
        self.scopes[(app_id, request.country)] = operation_id
        task = asyncio.create_task(self._run(app_id, request.country, operation))
        self.tasks.add(task)
        task.add_done_callback(self.tasks.discard)
        return self.get(operation_id)

    async def _run(self, app_id: int, country: str, operation: dict) -> None:
        operation["status"] = "running"
        try:
            await self.fetcher.collect(app_id, country, operation)
        except Exception:
            operation["status"] = "failed"
            operation["error"] = {"code": "UPSTREAM_ERROR", "message": "Apple's review collection could not be completed."}

    def get(self, operation_id: str) -> dict:
        self._prune()
        operation = self.operations.get(operation_id)
        if operation is None:
            raise SearchError(404, "OPERATION_NOT_FOUND", "This review collection operation is unavailable.")
        return {key: value for key, value in operation.items() if key != "createdAt"}
