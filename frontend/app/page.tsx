"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { errorMessages, normalizedQuery, type Catalog, type SearchIdentity, type SearchResponse, type Storefront } from "./api";

type Screen =
  | { kind: "initial" }
  | { kind: "loading"; submitted: SearchIdentity }
  | { kind: "success"; submitted: SearchIdentity; data: SearchResponse }
  | { kind: "error"; submitted: SearchIdentity; code: string; retryAfter: string | null };

export default function Discovery() {
  const [draft, setDraft] = useState("");
  const [country, setCountry] = useState<Storefront | null>(null);
  const [catalogFailed, setCatalogFailed] = useState(false);
  const [screen, setScreen] = useState<Screen>({ kind: "initial" });
  const sequence = useRef(0);
  const pending = useRef<AbortController | null>(null);

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/apps/storefronts", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Catalog unavailable");
        const catalog: Catalog = await response.json();
        const initial = catalog.storefronts.find((item) => item.code === catalog.defaultCountry);
        if (!initial || initial.code !== "us") throw new Error("US storefront unavailable");
        setCountry(initial);
      })
      .catch(() => { if (!controller.signal.aborted) setCatalogFailed(true); });
    return () => { controller.abort(); pending.current?.abort(); };
  }, []);

  async function search(submitted: SearchIdentity) {
    const current = ++sequence.current;
    pending.current?.abort();
    const controller = new AbortController();
    pending.current = controller;
    const query = normalizedQuery(submitted.phrase);
    if (Array.from(query).length < 2 || Array.from(query).length > 100) {
      setScreen({ kind: "error", submitted, code: "VALIDATION_ERROR", retryAfter: null });
      return;
    }
    setScreen({ kind: "loading", submitted });
    try {
      const params = new URLSearchParams({ q: query, country: submitted.country.code, limit: "50" });
      const response = await fetch(`/api/v1/apps/search?${params}`, { cache: "no-store", signal: controller.signal });
      const body = await response.json();
      if (current !== sequence.current) return;
      if (!response.ok) {
        const code = body?.error?.code;
        setScreen({ kind: "error", submitted, code: code in errorMessages ? code : "CONNECTION_ERROR", retryAfter: response.headers.get("retry-after") });
      } else {
        setScreen({ kind: "success", submitted, data: body as SearchResponse });
      }
    } catch {
      if (current === sequence.current && !controller.signal.aborted) {
        setScreen({ kind: "error", submitted, code: "CONNECTION_ERROR", retryAfter: null });
      }
    }
  }

  function submit(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    if (country) void search({ phrase: draft, country });
  }

  const error = screen.kind === "error" ? errorMessages[screen.code] : null;

  return (
    <>
      <a className="skip-link" href="#search">Skip to search</a>
      <header className="masthead">
        <span className="wordmark">bibi<span aria-hidden="true">.</span></span>
        <span className="local-label">Local workspace <span aria-hidden="true">/</span> App discovery</span>
      </header>
      <main>
        <div className="intro">
          <p className="eyebrow">Apple App Store · Keyword search</p>
          <h1>Find apps.<br /><span>Start with a keyword.</span></h1>
          <p className="lede">Explore listing matches for a market, problem, or idea. Discovery only—no saved research or review collection.</p>
        </div>
        <section className="search-panel" aria-label="Keyword search">
          <div className="search-context"><span className="eyebrow">Keyword</span><span>Storefront: <strong>{country?.name ?? "United States"} (US)</strong></span></div>
          <form onSubmit={submit} noValidate autoComplete="off">
            <label htmlFor="search">Search phrase</label>
            <div className="search-controls">
              <input id="search" name="keyword" type="search" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder="e.g. adhd planner" autoComplete="off" aria-describedby="search-help" aria-invalid={screen.kind === "error" && screen.code === "VALIDATION_ERROR"} />
              <button type="submit" disabled={!country}>Search <span aria-hidden="true">↗</span></button>
            </div>
            <p id="search-help" className="help">2–100 characters. Search or press Enter to submit. Typing never searches.</p>
          </form>
          {catalogFailed && <p role="alert" className="catalog-error">The storefront catalog could not load. Start the FastAPI server and reload this page.</p>}
        </section>
        <section className="search-output" aria-label="Search status and results" aria-busy={screen.kind === "loading"}>
          <div role="status" aria-live="polite" aria-atomic="true" className="status-line">
            {screen.kind === "initial" && "Ready when you are. No search has been submitted."}
            {screen.kind === "loading" && `Searching “${screen.submitted.phrase}” in ${screen.submitted.country.name}…`}
            {screen.kind === "success" && `${screen.data.results.length} displayed search results for “${screen.data.query}” in ${screen.submitted.country.name}.`}
          </div>
          {screen.kind === "initial" && <div className="empty-state"><span className="empty-marker" aria-hidden="true">01 / DISCOVER</span><h2>A phrase, then possibilities.</h2><p>Your matches will appear here in Apple’s returned order. Searches show up to 50 matches, not the entire App Store catalog.</p></div>}
          {screen.kind === "loading" && <div className="loading-lines" aria-hidden="true"><span /><span /><span /></div>}
          {screen.kind === "error" && error && <div role="alert" className="error-state">
            <p className="eyebrow">{screen.code.includes("RATE_LIMITED") ? "Rate limited" : "Search not completed"}</p>
            <h2>{error.title}</h2><p>{error.message}</p>
            <p className="search-identity">Submitted: “{screen.submitted.phrase}” · {screen.submitted.country.name} ({screen.submitted.country.code.toUpperCase()})</p>
            {screen.retryAfter && <p>Retry-After: {/^\d+$/.test(screen.retryAfter) ? `${screen.retryAfter} seconds from this response` : screen.retryAfter}. No automatic retry.</p>}
            {screen.code !== "VALIDATION_ERROR" && <button type="button" className="secondary" onClick={() => void search(screen.submitted)}>Retry submitted search</button>}
          </div>}
          {screen.kind === "success" && <>
            <div className="result-heading"><div><p className="eyebrow">{screen.submitted.country.name} · {screen.data.country.toUpperCase()}</p><h2>Matches for “{screen.data.query}”</h2></div><span className="result-count">{screen.data.results.length} displayed</span></div>
            <p className="result-note">Limited search matches · Up to 50 · Apple’s returned order, not a complete catalog.</p>
            <p className="fetch-info">Metadata fetched <time dateTime={screen.data.fetchedAt}>{new Date(screen.data.fetchedAt).toLocaleString()}</time> · {screen.data.cached ? "Cached metadata" : "Fresh from Apple · Not cached"}</p>
            {screen.data.results.length === 0 ? <div className="empty-state"><h3>No matches in this storefront.</h3><p>Apple returned no usable app matches. Try another phrase; no other country was substituted.</p></div> : <ol className="results">
              {screen.data.results.map((app) => <li key={app.appId}>
                <div className="listing-identity"><h3>{app.name ?? "App name unavailable"}</h3><p>{app.developer ?? "Developer unavailable"}</p><p className="app-id">Apple app ID <span>{app.appId}</span></p></div>
                {app.storeUrl ? <a className="listing-link" href={app.storeUrl} target="_blank" rel="noopener noreferrer" aria-label={`Open ${app.name ?? `app ${app.appId}`} on the App Store (new tab)`}>App Store <span aria-hidden="true">↗</span></a> : <span className="link-unavailable">Listing link unavailable</span>}
              </li>)}
            </ol>}
          </>}
        </section>
        <footer>Listing discovery, nothing more. Searches are not saved; reload to start fresh.</footer>
      </main>
    </>
  );
}
