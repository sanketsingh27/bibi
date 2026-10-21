from urllib.parse import urlsplit

from pydantic import BaseModel

MAX_SAFE_INTEGER = 2**53 - 1


class Listing(BaseModel):
    appId: int
    name: str | None
    developer: str | None
    iconUrl: str | None
    averageRating: float | None
    ratingCount: int | None
    category: str | None
    storeUrl: str | None
    country: str


class SearchResponse(BaseModel):
    query: str
    country: str
    fetchedAt: str
    cached: bool
    results: list[Listing]


class Storefront(BaseModel):
    code: str
    name: str


class StorefrontResponse(BaseModel):
    defaultCountry: str
    storefronts: list[Storefront]


class ErrorDetail(BaseModel):
    code: str
    message: str


class ErrorResponse(BaseModel):
    error: ErrorDetail


def text(value: object) -> str | None:
    return value if isinstance(value, str) and value.strip() else None


def safe_url(value: object, *, listing: bool = False) -> str | None:
    if not isinstance(value, str) or any(char.isspace() or ord(char) < 32 for char in value) or "\\" in value:
        return None
    try:
        parsed = urlsplit(value)
        if (parsed.scheme != "https" or not parsed.hostname or parsed.username is not None
                or parsed.password is not None or parsed.port not in (None, 443)):
            return None
        host = parsed.hostname.encode("idna").decode("ascii")
        if listing and host not in ("apps.apple.com", "itunes.apple.com"):
            return None
        if not all(label and all(char.isalnum() or char == "-" for char in label) for label in host.split(".")):
            return None
    except (ValueError, UnicodeError):
        return None
    return value


def normalize_results(records: list[dict], country: str, limit: int) -> list[Listing]:
    results = []
    seen = set()
    for record in records:
        app_id = record.get("trackId")
        if (record.get("kind") != "software" or type(app_id) is not int
                or not 0 < app_id <= MAX_SAFE_INTEGER or app_id in seen):
            continue
        seen.add(app_id)
        average = record.get("averageUserRating")
        if type(average) not in (int, float) or not 0 <= average <= 5:
            average = None
        count = record.get("userRatingCount")
        if type(count) is not int or not 0 <= count <= MAX_SAFE_INTEGER:
            count = None
        results.append(Listing(
            appId=app_id,
            name=text(record.get("trackName")),
            developer=text(record.get("artistName")),
            iconUrl=safe_url(record.get("artworkUrl100")) or safe_url(record.get("artworkUrl60")),
            averageRating=average,
            ratingCount=count,
            category=text(record.get("primaryGenreName")),
            storeUrl=safe_url(record.get("trackViewUrl"), listing=True),
            country=country,
        ))
        if len(results) == limit:
            break
    return results
