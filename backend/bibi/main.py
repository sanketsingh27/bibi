import re
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Annotated, Protocol
from urllib.parse import urlsplit

import httpx
from fastapi import FastAPI, Query, Request, Response
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .credentials import CredentialStoreUnavailable, MacOSCredentialStore
from .models import ErrorResponse, SearchResponse, StorefrontResponse
from .search import SearchError, SearchService
from .storefronts import STOREFRONTS


LOOPBACK_HOSTS = frozenset({"127.0.0.1", "localhost", "::1"})


class SearchParams(BaseModel):
    model_config = ConfigDict(extra="forbid")
    q: str
    country: str = "us"
    limit: int = Field(default=50, ge=1, le=50)

    @field_validator("q")
    @classmethod
    def normalize_query(cls, value: str) -> str:
        normalized = " ".join(value.split())
        if not 2 <= len(normalized) <= 100:
            raise ValueError("Search must contain 2–100 characters after whitespace normalization.")
        return normalized

    @field_validator("country")
    @classmethod
    def normalize_country(cls, value: str) -> str:
        country = value.strip().lower()
        if country not in STOREFRONTS:
            raise ValueError("Unsupported App Store country.")
        return country

    @field_validator("limit", mode="before")
    @classmethod
    def integer_limit(cls, value: object) -> object:
        if isinstance(value, str) and re.fullmatch(r"[+-]?[0-9]+", value) is None:
            raise ValueError("Limit must be an integer from 1–50.")
        return value


class CredentialStore(Protocol):
    @property
    def available(self) -> bool: ...

    def get(self) -> str | None: ...
    def set(self, value: str) -> None: ...
    def delete(self) -> None: ...


class AISettingsInput(BaseModel):
    model_config = ConfigDict(extra="forbid")
    apiKey: str = Field(min_length=29, max_length=4096)

    @field_validator("apiKey")
    @classmethod
    def valid_key_shape(cls, value: str) -> str:
        if re.fullmatch(r"sk-or-v1-[A-Za-z0-9_-]{20,4087}", value.strip()) is None:
            raise ValueError("Enter a valid OpenRouter API key.")
        return value.strip()


def local_request_allowed(request: Request) -> bool:
    try:
        host = urlsplit(f"//{request.headers.get('host', '')}").hostname
        if host not in LOOPBACK_HOSTS:
            return False
        origin = request.headers.get("origin")
        if origin is not None:
            parsed = urlsplit(origin)
            if parsed.scheme != "http" or parsed.hostname not in LOOPBACK_HOSTS or parsed.path or parsed.query or parsed.fragment:
                return False
        if request.headers.get("sec-fetch-site") in {"cross-site", "same-site"}:
            return False
        return True
    except ValueError:
        return False


def create_app(*, apple_transport: httpx.AsyncBaseTransport | None = None,
               clock: Callable[[], float] = time.monotonic,
               credential_store: CredentialStore | None = None) -> FastAPI:
    store = credential_store or MacOSCredentialStore()

    @asynccontextmanager
    async def lifespan(app: FastAPI):
        # HTTPX verifies TLS by default, follows no redirects, and makes no automatic retries.
        async with httpx.AsyncClient(transport=apple_transport, timeout=8, follow_redirects=False) as client:
            app.state.search = SearchService(client, clock)
            try:
                yield
            finally:
                await app.state.search.aclose()

    app = FastAPI(title="Bibi App discovery", lifespan=lifespan)

    @app.middleware("http")
    async def response_headers(request: Request, call_next):
        protected = (
            request.method == "PUT" and request.url.path == "/api/v1/ai/settings"
        ) or (
            request.method == "DELETE" and request.url.path == "/api/v1/ai/key"
        )
        if protected and not local_request_allowed(request):
            response = JSONResponse(status_code=403, content={"error": {
                "code": "LOCAL_REQUEST_FORBIDDEN", "message": "This local request is not allowed.",
            }})
        else:
            response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {
            "code": "VALIDATION_ERROR",
            "message": "Request fields or values are invalid.",
        }})

    @app.exception_handler(SearchError)
    async def search_error(request: Request, error: SearchError):
        return JSONResponse(status_code=error.status, content={"error": {
            "code": error.code, "message": error.message,
        }}, headers={"Retry-After": error.retry_after} if error.retry_after is not None else {})

    @app.get("/api/v1/ai/settings")
    async def ai_settings():
        try:
            has_key = store.get() is not None
            available = store.available
        except Exception:
            has_key, available = False, False
        return {
            "hasKey": has_key,
            "selectedModelId": None,
            "storeStatus": "available" if available else "unavailable",
        }

    @app.put("/api/v1/ai/settings")
    async def save_ai_settings(settings: AISettingsInput):
        try:
            if not store.available:
                raise CredentialStoreUnavailable
            store.set(settings.apiKey)
        except Exception:
            return JSONResponse(status_code=503, content={"error": {
                "code": "CREDENTIAL_STORE_UNAVAILABLE",
                "message": "The macOS Keychain is unavailable or locked. No changes were saved.",
            }})
        return {"hasKey": True, "selectedModelId": None, "storeStatus": "available"}

    @app.delete("/api/v1/ai/key", status_code=204)
    async def delete_ai_key():
        try:
            if not store.available:
                raise CredentialStoreUnavailable
            store.delete()
        except Exception:
            return JSONResponse(status_code=503, content={"error": {
                "code": "CREDENTIAL_STORE_UNAVAILABLE",
                "message": "The macOS Keychain is unavailable or locked. No changes were made.",
            }})
        return Response(status_code=204)

    @app.get("/api/v1/apps/storefronts", response_model=StorefrontResponse)
    async def storefronts():
        return {"defaultCountry": "us", "storefronts": [
            {"code": code, "name": name} for code, name in STOREFRONTS.items()
        ]}

    @app.get("/api/v1/apps/search", response_model=SearchResponse,
             responses={status: {"model": ErrorResponse} for status in (422, 429, 502, 504)})
    async def search(request: Request, params: Annotated[SearchParams, Query()]):
        if any(len(request.query_params.getlist(key)) != 1 for key in request.query_params):
            raise RequestValidationError([])
        return await request.app.state.search.search(params.q, params.country, params.limit)

    return app


app = create_app()
