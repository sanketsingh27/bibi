export type Storefront = { code: string; name: string };
export type Catalog = { defaultCountry: string; storefronts: Storefront[] };
export type Listing = {
  appId: number;
  name: string | null;
  developer: string | null;
  iconUrl: string | null;
  averageRating: number | null;
  ratingCount: number | null;
  category: string | null;
  storeUrl: string | null;
  country: string;
};
export type SearchResponse = {
  query: string;
  country: string;
  fetchedAt: string;
  cached: boolean;
  results: Listing[];
};
export type AppDetailsResponse = Listing & { fetchedAt: string; cached: boolean };
export type SearchIdentity = { phrase: string; country: Storefront };

export const errorMessages: Record<string, { title: string; message: string }> = {
  VALIDATION_ERROR: { title: "Check your search", message: "Enter 2–100 characters after whitespace normalization. Use a supported storefront and a limit from 1–50." },
  SEARCH_RATE_LIMITED: { title: "Search budget reached", message: "This local API allows 10 Apple requests per rolling minute, including failed attempts." },
  UPSTREAM_RATE_LIMITED: { title: "Apple is limiting searches", message: "Apple declined this request. Try again manually later." },
  UPSTREAM_TIMEOUT: { title: "Apple search timed out", message: "Apple did not complete the search within the deadline. This is not a no-match result." },
  UPSTREAM_ERROR: { title: "Apple search unavailable", message: "Apple could not complete this search. This is not a no-match result." },
  CONNECTION_ERROR: { title: "Cannot reach the search API", message: "Check that the local FastAPI server is running, then retry manually." },
};

// Matches Python str.split whitespace, including its ASCII record separators.
export function normalizedQuery(value: string) {
  return value.replace(/[\p{White_Space}\u001c-\u001f]+/gu, " ").replace(/^ +| +$/g, "");
}
