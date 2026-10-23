"use client";

import { useEffect, useRef, useState } from "react";
import { errorMessages, type AppDetailsResponse } from "./api";
import { ListingRow } from "./listing-row";
import { DetailContent } from "./detail-content";
import { detailSnapshot, validatedDetails } from "./detail-snapshot";

export type DetailIdentity = { appId: string; country: string; invalid: boolean };
type DetailScreen =
  | { kind: "loading" }
  | { kind: "success"; data: AppDetailsResponse; saved: boolean; lookupError?: string }
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
  const [storageMessage, setStorageMessage] = useState("");
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
    setStorageMessage("");
    async function failure(code: string, retryAfter: string | null) {
      if (controller.signal.aborted) return;
      if (code !== "VALIDATION_ERROR") {
        try {
          const saved = validatedDetails(await detailSnapshot(Number(identity.appId), identity.country), Number(identity.appId), identity.country);
          if (controller.signal.aborted) return;
          if (saved) {
            setScreen({ kind: "success", data: saved, saved: true, lookupError: code });
            return;
          }
        } catch {
          if (!controller.signal.aborted) setStorageMessage("Local snapshot storage unavailable. No saved fallback could be read.");
        }
      }
      if (!controller.signal.aborted) setScreen({ kind: "error", code, retryAfter });
    }
    const params = new URLSearchParams({ country: identity.country });
    fetch(`/api/v1/apps/${identity.appId}?${params}`, { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        const body: unknown = await response.json();
        if (controller.signal.aborted) return;
        if (!response.ok) {
          const code = (body as { error?: { code?: unknown } })?.error?.code;
          await failure(typeof code === "string" ? code : "CONNECTION_ERROR", response.headers.get("retry-after"));
          return;
        }
        const data = validatedDetails(body, Number(identity.appId), identity.country);
        if (!data) { await failure("UPSTREAM_ERROR", null); return; }
        setScreen({ kind: "success", data, saved: false });
        try {
          await detailSnapshot(data.appId, data.country, data);
          if (!controller.signal.aborted) setStorageMessage("Listing snapshot saved on this device. Metadata and URLs only.");
        } catch {
          if (!controller.signal.aborted) setStorageMessage("Could not save this listing on this device. Live details remain available.");
        }
      })
      .catch(() => { void failure("CONNECTION_ERROR", null); });
    return () => controller.abort();
  }, [identity.appId, identity.country, identity.invalid, attempt]);

  const error = screen.kind === "error" ? detailErrors[screen.code] ?? errorMessages.CONNECTION_ERROR : null;

  return <main className="app-details" id="app-details" ref={content} tabIndex={-1}>
    <button type="button" className="secondary" onClick={onBack}>Back to search</button>
    <p className="eyebrow detail-scope">Apple App Store · Storefront: {identity.country.toUpperCase() || "Unavailable"} · App ID {identity.appId || "Unavailable"}</p>
    <section aria-label="Exact app listing" aria-busy={screen.kind === "loading"}>
      <div role="status" aria-live="polite" className="status-line">
        {screen.kind === "loading" ? "Loading the exact app listing…" : screen.kind === "success" ? (screen.saved ? "Saved listing snapshot. Live lookup failed." : "Exact listing loaded.") : "Listing lookup not completed."}
      </div>
      {screen.kind === "loading" && <h1>Loading app details…</h1>}
      {screen.kind === "error" && error && <div className="error-state" role="alert">
        <h1>{error.title}</h1><p>{error.message}</p>
        {screen.retryAfter && <p>Retry-After: {screen.retryAfter}. No automatic retry.</p>}
        {screen.code !== "VALIDATION_ERROR" && <button type="button" className="secondary" onClick={() => setAttempt((value) => value + 1)}>Retry exact lookup</button>}
      </div>}
      {screen.kind === "success" && <>
        {screen.saved && <div className="saved-notice" role="status"><strong>Saved snapshot · Live lookup failed</strong><p>{(detailErrors[screen.lookupError ?? ""] ?? errorMessages.CONNECTION_ERROR).message} Showing previously saved metadata for this exact app and storefront.</p><button type="button" className="secondary" onClick={() => setAttempt((value) => value + 1)}>Retry exact lookup</button></div>}
        <ul className="results"><ListingRow key={`${screen.data.appId}:${screen.data.country}:${screen.data.fetchedAt}`} app={screen.data} heading="h1" /></ul>
        <p className="result-note">Listing ratings belong to the {screen.data.country.toUpperCase()} storefront. Ratings are not written reviews.</p>
        <p className="fetch-info">Metadata fetched <time dateTime={screen.data.fetchedAt}>{new Date(screen.data.fetchedAt).toLocaleString()}</time> · {screen.saved ? "Saved on this device · Not live metadata" : screen.data.cached ? "Cached metadata" : "Fresh from Apple · Not cached"}</p>
        <DetailContent app={screen.data} />
      </>}
    </section>
    {storageMessage && <p className="fetch-info" role="status">{storageMessage}</p>}
    <footer>Apple, the Apple logo, and App Store are trademarks of Apple Inc., registered in the U.S. and other countries.</footer>
  </main>;
}
