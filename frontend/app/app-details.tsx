"use client";

import { useEffect, useRef, useState } from "react";
import { errorMessages, type AppDetailsResponse } from "./api";
import { ListingRow } from "./listing-row";

export type DetailIdentity = { appId: string; country: string; invalid: boolean };
type DetailScreen =
  | { kind: "loading" }
  | { kind: "success"; data: AppDetailsResponse }
  | { kind: "error"; code: string; retryAfter: string | null };

const detailErrors: Record<string, { title: string; message: string }> = {
  ...errorMessages,
  VALIDATION_ERROR: { title: "Invalid app identity", message: "Use a positive safe-integer Apple app ID and a supported lowercase country storefront." },
  APP_UNAVAILABLE: { title: "App unavailable", message: "This exact app was not found in this storefront. No other app or country was substituted." },
  UPSTREAM_RATE_LIMITED: { title: "Apple is limiting requests", message: "Apple declined this lookup. Try again manually later." },
  UPSTREAM_TIMEOUT: { title: "Apple lookup timed out", message: "Apple did not complete the lookup within the deadline. This does not mean the app is unavailable." },
  UPSTREAM_ERROR: { title: "Apple lookup failed", message: "Apple could not complete this lookup. Try again manually." },
};

export function AppDetails({ identity, onBack }: { identity: DetailIdentity; onBack: () => void }) {
  const [screen, setScreen] = useState<DetailScreen>({ kind: "loading" });
  const [attempt, setAttempt] = useState(0);
  const content = useRef<HTMLElement | null>(null);

  useEffect(() => {
    content.current?.focus();
    const controller = new AbortController();
    if (identity.invalid || !/^[0-9]{1,16}$/.test(identity.appId)
        || !Number.isSafeInteger(Number(identity.appId)) || Number(identity.appId) <= 0
        || !/^[a-z]{2}$/.test(identity.country)) {
      setScreen({ kind: "error", code: "VALIDATION_ERROR", retryAfter: null });
      return () => controller.abort();
    }
    setScreen({ kind: "loading" });
    const params = new URLSearchParams({ country: identity.country });
    fetch(`/api/v1/apps/${identity.appId}?${params}`, { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const body = await response.json();
        if (controller.signal.aborted) return;
        if (!response.ok) {
          setScreen({ kind: "error", code: body?.error?.code ?? "CONNECTION_ERROR", retryAfter: response.headers.get("retry-after") });
        } else if (body.appId !== Number(identity.appId) || body.country !== identity.country) {
          setScreen({ kind: "error", code: "APP_UNAVAILABLE", retryAfter: null });
        } else {
          setScreen({ kind: "success", data: body as AppDetailsResponse });
        }
      })
      .catch(() => {
        if (!controller.signal.aborted) setScreen({ kind: "error", code: "CONNECTION_ERROR", retryAfter: null });
      });
    return () => controller.abort();
  }, [identity.appId, identity.country, identity.invalid, attempt]);

  const error = screen.kind === "error" ? detailErrors[screen.code] ?? errorMessages.CONNECTION_ERROR : null;

  return <main className="app-details" id="app-details" ref={content} tabIndex={-1}>
    <button type="button" className="secondary" onClick={onBack}>Back to search</button>
    <p className="eyebrow detail-scope">Apple App Store · Storefront: {identity.country.toUpperCase() || "Unavailable"} · App ID {identity.appId || "Unavailable"}</p>
    <section aria-label="Exact app listing" aria-busy={screen.kind === "loading"}>
      <div role="status" aria-live="polite" className="status-line">
        {screen.kind === "loading" ? "Loading the exact app listing…" : screen.kind === "success" ? "Exact listing loaded." : "Listing lookup not completed."}
      </div>
      {screen.kind === "loading" && <h1>Loading app details…</h1>}
      {screen.kind === "error" && error && <div className="error-state" role="alert">
        <h1>{error.title}</h1><p>{error.message}</p>
        {screen.retryAfter && <p>Retry-After: {screen.retryAfter}. No automatic retry.</p>}
        {screen.code !== "VALIDATION_ERROR" && <button type="button" className="secondary" onClick={() => setAttempt((value) => value + 1)}>Retry exact lookup</button>}
      </div>}
      {screen.kind === "success" && <>
        <ul className="results"><ListingRow app={screen.data} heading="h1" /></ul>
        <p className="result-note">Listing ratings belong to the {screen.data.country.toUpperCase()} storefront. Ratings are not written reviews.</p>
        <p className="fetch-info">Metadata fetched <time dateTime={screen.data.fetchedAt}>{new Date(screen.data.fetchedAt).toLocaleString()}</time> · {screen.data.cached ? "Cached metadata" : "Fresh from Apple · Not cached"}</p>
      </>}
    </section>
    <footer>Apple, the Apple logo, and App Store are trademarks of Apple Inc., registered in the U.S. and other countries.</footer>
  </main>;
}
