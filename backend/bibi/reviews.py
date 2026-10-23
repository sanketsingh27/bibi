import asyncio
import secrets
from collections.abc import Callable
from datetime import datetime, timedelta, timezone
from email.utils import parsedate_to_datetime
from typing import Literal

import httpx
from pydantic import BaseModel, ConfigDict, Field

from .search import SearchError, SearchService, valid_retry_after
from .storefronts import STOREFRONTS


class ReviewFetchInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    requestId: str = Field(min_length=1, max_length=128)
    country: str
    targetCount: Literal[200, 500]


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


def _retry_delay(value: str | None) -> int | None:
    value = valid_retry_after(value)
    if value is None:
        return None
    if value.isdecimal():
        return min(int(value), 86400)
    try:
        return max(0, min(86400, int((parsedate_to_datetime(value) - datetime.now(timezone.utc)).total_seconds())))
    except (ValueError, TypeError, OverflowError):
        return None


class ReviewFetcher:
    def __init__(self, client: httpx.AsyncClient, search: SearchService):
        self.client = client
        self.search = search

    async def collect(self, app_id: int, country: str, operation: dict) -> None:
        completed_pages: set[int] = operation["completedPages"]
        records: dict[str, dict] = operation["records"]
        page_gaps: set[int] = operation["pageGaps"]
        warnings: dict[int, str] = operation["warnings"]
        failed = False
        rate_limited = False
        for page in range(1, 11):
            if len(records) >= operation["targetCount"]:
                break
            if page in completed_pages:
                continue
            operation["progress"].update(currentPage=page)
            try:
                await self.search.reserve_review_dispatch()
                operation["attempts"] += 1
                operation["progress"]["pagesAttempted"] = operation["attempts"]
                fetched_at = datetime.now(timezone.utc).isoformat().replace("+00:00", "Z")
                url = f"https://itunes.apple.com/{country}/rss/customerreviews/page={page}/id={app_id}/sortby=mostrecent/json"
                async with asyncio.timeout(8):
                    response = await self.client.get(url)
                if response.status_code == 429:
                    delay = _retry_delay(response.headers.get("retry-after"))
                    operation["error"] = {"code": "UPSTREAM_RATE_LIMITED",
                                           "message": "Apple is limiting review requests. Resume manually after the indicated wait."}
                    operation["resumeAt"] = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat().replace("+00:00", "Z") if delay is not None else None
                    operation["resumeAfter"] = self.search.clock() + delay if delay is not None else None
                    rate_limited = True
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
            except SearchError as error:
                operation["error"] = {"code": error.code, "message": error.message}
                delay = _retry_delay(error.retry_after)
                operation["resumeAt"] = (datetime.now(timezone.utc) + timedelta(seconds=delay)).isoformat().replace("+00:00", "Z") if delay is not None else None
                operation["resumeAfter"] = self.search.clock() + delay if delay is not None else None
                rate_limited = error.status == 429
                failed = not rate_limited
                break
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
                if review.reviewId in records:
                    continue
                records[review.reviewId] = review.model_dump()
                page_records += 1
                if len(records) >= operation["targetCount"]:
                    break
            completed_pages.add(page)
            if page_records == 0:
                page_gaps.add(page)
            if invalid_records:
                warnings[page] = f"Page {page}: excluded {invalid_records} malformed written review record(s)."
            operation["progress"].update(count=len(records), pagesAttempted=operation["attempts"],
                                          pageGaps=sorted(page_gaps), completedPages=sorted(completed_pages))

        if failed:
            operation["status"] = "partial" if records else "failed"
        elif rate_limited:
            operation["status"] = "rate-limited"
        else:
            operation["status"] = "succeeded"
        operation["progress"].update(currentPage=None, count=len(records), pagesAttempted=operation["attempts"],
                                      pageGaps=sorted(page_gaps), completedPages=sorted(completed_pages))
        operation["result"] = self.result(app_id, country, operation)

    def result(self, app_id: int, country: str, operation: dict) -> dict:
        records = list(operation["records"].values())[:operation["targetCount"]]
        status = operation["status"]
        failed = status in {"partial", "failed", "rate-limited", "cancelled"}
        return {
            "appId": app_id, "country": country, "targetCount": operation["targetCount"],
            "count": len(records), "targetReached": len(records) >= operation["targetCount"],
            "reviews": records, "pagesAttempted": operation["attempts"],
            "pageGaps": sorted(operation["pageGaps"]), "warnings": list(operation["warnings"].values()),
            "sourceAvailability": "available" if records and not failed else
                                 "partial" if records else "unavailable" if status != "succeeded" else "empty",
        }


class ReviewOperationManager:
    ACTIVE = {"queued", "running"}
    RESUMABLE = {"partial", "cancelled", "rate-limited"}

    def __init__(self, fetcher: ReviewFetcher, clock: Callable[[], float]):
        self.fetcher = fetcher
        self.clock = clock
        self.operations: dict[str, dict] = {}
        self.requests: dict[str, tuple[tuple[int, str, int], str]] = {}
        self.scopes: dict[tuple[int, str], str] = {}
        self.tasks: dict[str, asyncio.Task] = {}

    def _prune(self) -> None:
        now = self.clock()
        expired = [key for key, value in self.operations.items()
                   if value["status"] not in self.ACTIVE and now - value["createdAt"] > 3600]
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

        scope = (app_id, request.country)
        previous_id = self.scopes.get(scope)
        previous = self.operations.get(previous_id) if previous_id else None
        if previous and previous["status"] in self.ACTIVE:
            if request.targetCount > previous["targetCount"]:
                raise SearchError(409, "OPERATION_CONFLICT", "A different target is already active for this app and storefront.")
            self.requests[request.requestId] = (payload, previous_id)
            return self.get(previous_id)
        if previous and previous["targetCount"] >= request.targetCount and previous["status"] != "failed":
            self.requests[request.requestId] = (payload, previous_id)
            return self.get(previous_id)
        if sum(value["status"] in self.ACTIVE for value in self.operations.values()) >= 2:
            raise SearchError(429, "SEARCH_RATE_LIMITED", "Two review collections are already active. Retry manually later.")

        operation_id = secrets.token_urlsafe(24)
        completed = set(previous["completedPages"]) if previous and request.targetCount >= previous["targetCount"] else set()
        records = dict(previous["records"]) if completed else {}
        page_gaps = set(previous["pageGaps"]) if completed else set()
        warnings = dict(previous["warnings"]) if completed else {}
        attempts = previous["attempts"] if completed else 0
        operation = {
            "operationId": operation_id, "kind": "review-fetch", "status": "queued",
            "scope": {"appId": app_id, "country": request.country}, "targetCount": request.targetCount,
            "progress": {"count": len(records), "targetCount": request.targetCount,
                         "pagesAttempted": attempts, "currentPage": None,
                         "pageGaps": sorted(page_gaps), "completedPages": sorted(completed)},
            "result": None, "error": None, "resumeAt": None, "resumeAfter": None,
            "createdAt": self.clock(), "completedPages": completed, "attempts": attempts, "records": records,
            "pageGaps": page_gaps, "warnings": warnings,
        }
        self.operations[operation_id] = operation
        self.requests[request.requestId] = (payload, operation_id)
        self.scopes[scope] = operation_id
        self._launch(app_id, request.country, operation)
        return self.get(operation_id)

    def _launch(self, app_id: int, country: str, operation: dict) -> None:
        task = asyncio.create_task(self._run(app_id, country, operation))
        self.tasks[operation["operationId"]] = task
        task.add_done_callback(lambda done, operation_id=operation["operationId"]: self.tasks.pop(operation_id, None))

    async def _run(self, app_id: int, country: str, operation: dict) -> None:
        operation["status"] = "running"
        operation["error"] = None
        try:
            await self.fetcher.collect(app_id, country, operation)
        except asyncio.CancelledError:
            operation["status"] = "cancelled"
            operation["progress"].update(currentPage=None, count=len(operation["records"]))
            operation["result"] = self.fetcher.result(app_id, country, operation)
        except Exception:
            operation["status"] = "partial" if operation["records"] else "failed"
            operation["error"] = {"code": "UPSTREAM_ERROR", "message": "Apple's review collection could not be completed."}
            operation["progress"].update(currentPage=None, count=len(operation["records"]))
            operation["result"] = self.fetcher.result(app_id, country, operation)

    def cancel(self, operation_id: str) -> dict:
        operation = self._operation(operation_id)
        if operation["status"] not in self.ACTIVE:
            return self.get(operation_id)
        task = self.tasks.get(operation_id)
        if task is not None:
            task.cancel()
        else:
            operation["status"] = "cancelled"
            app_id, country = operation["scope"]["appId"], operation["scope"]["country"]
            operation["result"] = self.fetcher.result(app_id, country, operation)
        return self.get(operation_id)

    def resume(self, operation_id: str) -> dict:
        operation = self._operation(operation_id)
        if operation["status"] not in self.RESUMABLE:
            raise SearchError(409, "OPERATION_CONFLICT", "Only a cancelled or partial collection can be resumed.")
        resume_after = operation.get("resumeAfter")
        if resume_after is not None and self.clock() < resume_after:
            remaining = max(1, int(resume_after - self.clock()))
            raise SearchError(429, "UPSTREAM_RATE_LIMITED", "Apple asked this collection to pause. Resume after the indicated time.", str(remaining))
        operation["status"] = "queued"
        operation["error"] = None
        operation["resumeAt"] = None
        operation["resumeAfter"] = None
        app_id, country = operation["scope"]["appId"], operation["scope"]["country"]
        self._launch(app_id, country, operation)
        return self.get(operation_id)

    def _operation(self, operation_id: str) -> dict:
        self._prune()
        operation = self.operations.get(operation_id)
        if operation is None:
            raise SearchError(404, "OPERATION_NOT_FOUND", "This review collection is unknown or no longer available in this process. Start a new explicit collection; lost work was not resubmitted.")
        return operation

    def get(self, operation_id: str) -> dict:
        operation = self._operation(operation_id)
        return {key: value for key, value in operation.items()
                if key not in {"createdAt", "completedPages", "records", "pageGaps", "warnings", "resumeAfter"}}
