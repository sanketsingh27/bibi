import re
import time
from collections.abc import Callable
from contextlib import asynccontextmanager
from typing import Annotated

import httpx
from fastapi import FastAPI, Query, Request
from fastapi.exceptions import RequestValidationError
from fastapi.responses import JSONResponse
from pydantic import BaseModel, ConfigDict, Field, field_validator

from .models import ErrorResponse, SearchResponse, StorefrontResponse
from .search import SearchError, SearchService
from .storefronts import STOREFRONTS


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


def create_app(*, apple_transport: httpx.AsyncBaseTransport | None = None,
               clock: Callable[[], float] = time.monotonic) -> FastAPI:
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
        response = await call_next(request)
        response.headers["Cache-Control"] = "no-store"
        response.headers["X-Content-Type-Options"] = "nosniff"
        return response

    @app.exception_handler(RequestValidationError)
    async def invalid_input(request: Request, error: RequestValidationError):
        return JSONResponse(status_code=422, content={"error": {
            "code": "VALIDATION_ERROR",
            "message": "Use a 2–100-character search, a supported country, and an integer limit from 1–50. Only q, country and limit are accepted.",
        }})

    @app.exception_handler(SearchError)
    async def search_error(request: Request, error: SearchError):
        return JSONResponse(status_code=error.status, content={"error": {
            "code": error.code, "message": error.message,
        }}, headers={"Retry-After": error.retry_after} if error.retry_after is not None else {})

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
