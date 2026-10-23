"use client";

import { useEffect, useRef, useState, type FormEvent } from "react";
import { errorMessages, normalizedQuery, type Catalog, type SearchIdentity, type SearchResponse, type Storefront } from "./api";
import { Settings } from "./settings";
import { ListingRow } from "./listing-row";
import { AppDetails, type DetailIdentity } from "./app-details";
import { listSavedResearch, type SavedSample } from "./research-library";

type Screen =
  | { kind: "initial" }
  | { kind: "loading"; submitted: SearchIdentity }
  | { kind: "success"; submitted: SearchIdentity; data: SearchResponse }
  | { kind: "error"; submitted: SearchIdentity; code: string; retryAfter: string | null };

export default function Discovery() {
  const [draft, setDraft] = useState("");
  const [mode, setMode] = useState<"keyword" | "app-name">("keyword");
  const [country, setCountry] = useState<Storefront | null>(null);
  const [storefronts, setStorefronts] = useState<Storefront[]>([]);
  const [catalogFailed, setCatalogFailed] = useState(false);
  const [screen, setScreen] = useState<Screen>({ kind: "initial" });
  const sequence = useRef(0);
  const pending = useRef<AbortController | null>(null);
  const [detail, setDetail] = useState<DetailIdentity | null>(null);
  const [locationReady, setLocationReady] = useState(false);
  const [savedResearch, setSavedResearch] = useState<SavedSample[]>([]);
  const openedFromSearch = useRef(false);
  const selectionButton = useRef<HTMLButtonElement | null>(null);

  useEffect(() => {
    function readLocation() {
      const params = new URLSearchParams(window.location.search);
      setDetail(params.has("appId") || params.has("country") ? {
        appId: params.get("appId") ?? "", country: params.get("country") ?? "",
        invalid: params.getAll("appId").length !== 1 || params.getAll("country").length !== 1,
        saved: params.get("saved") === "1",
      } : null);
      setLocationReady(true);
    }
    readLocation();
    window.addEventListener("popstate", readLocation);
    return () => window.removeEventListener("popstate", readLocation);
  }, []);

  useEffect(() => {
    let active = true;
    const load = () => void listSavedResearch().then((items) => { if (active) setSavedResearch(items); }).catch(() => { if (active) setSavedResearch([]); });
    load();
    window.addEventListener("bibi:saved-research-changed", load);
    return () => { active = false; window.removeEventListener("bibi:saved-research-changed", load); };
  }, [detail]);

  useEffect(() => {
    if (locationReady && !detail) selectionButton.current?.focus();
  }, [detail, locationReady]);

  function openDetails(appId: number, storefront: string, button: HTMLButtonElement, saved = false) {
    selectionButton.current = button;
    openedFromSearch.current = true;
    const params = new URLSearchParams({ appId: String(appId), country: storefront, ...(saved ? { saved: "1" } : {}) });
    window.history.pushState(null, "", `?${params}`);
    setDetail({ appId: String(appId), country: storefront, invalid: false, saved });
  }

  function backToSearch() {
    if (openedFromSearch.current) {
      window.history.back();
    } else {
      window.history.replaceState(null, "", "/");
      setDetail(null);
    }
  }

  useEffect(() => {
    const controller = new AbortController();
    fetch("/api/v1/apps/storefronts", { cache: "no-store", signal: controller.signal })
      .then(async (response) => {
        if (!response.ok) throw new Error("Catalog unavailable");
        const catalog: Catalog = await response.json();
        const initial = catalog.storefronts.find((item) => item.code === catalog.defaultCountry);
        if (!initial || initial.code !== "us") throw new Error("US storefront unavailable");
        setStorefronts(catalog.storefronts);
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

  function changeCountry(code: string) {
    const next = storefronts.find((item) => item.code === code);
    if (!next || next.code === country?.code) return;
    setCountry(next);
    if (screen.kind !== "initial") void search({ phrase: screen.submitted.phrase, country: next });
  }

  const error = screen.kind === "error" ? errorMessages[screen.code] : null;

  function changeMode(next: typeof mode) {
    setMode(next);
  }

  return (
    <>
      <a className="skip-link" href={detail ? "#app-details" : "#search"}>{detail ? "Skip to app details" : "Skip to search"}</a>
      <header className="masthead">
        <span className="wordmark">bibi<span aria-hidden="true">.</span></span>
        <span className="local-label">Local workspace <span aria-hidden="true">/</span> {detail ? "App details" : "App discovery"}</span>
      </header>
      {detail && <AppDetails key={`${detail.appId}:${detail.country}:${detail.invalid}`} identity={detail} onBack={backToSearch} />}
      <main hidden={Boolean(detail) || !locationReady}>
        <div className="intro">
          <p className="eyebrow">Apple App Store · App discovery</p>
          <h1>Find apps.<br /><span>Search a keyword or app name.</span></h1>
          <p className="lede">Explore listing matches for a market, problem, or known app. Select the intended listing to inspect its details.</p>
        </div>
        <section className="search-panel" aria-label="App discovery search">
          {savedResearch.length > 0 && <section aria-labelledby="saved-research-title" className="saved-research">
            <h2 id="saved-research-title">Saved research</h2>
            <ul className="saved-research-list">{savedResearch.map((sample) => <li key={`${sample.appId}:${sample.country}`}>
              <button type="button" className="secondary" onClick={(event) => openDetails(sample.appId, sample.country, event.currentTarget, true)}>
                {sample.listing.name ?? `App ${sample.appId}`} · {sample.country.toUpperCase()} · {sample.reviews.length} saved reviews
              </button>
            </li>)}</ul>
          </section>}
          <div className="search-context"><span className="eyebrow">{mode === "keyword" ? "Keyword" : "App name"}</span><span>Storefront: <strong>{country ? `${country.name} (${country.code.toUpperCase()})` : catalogFailed ? "Unavailable" : "Loading catalog…"}</strong></span></div>
          <div className="storefront-control">
            <label htmlFor="country">Country storefront</label>
            <select id="country" name="country" value={country?.code ?? ""} disabled={!country} onChange={(event) => changeCountry(event.target.value)} aria-describedby="country-help">
              {!country && <option value="">{catalogFailed ? "Catalog unavailable" : "Loading storefronts…"}</option>}
              {storefronts.map((item) => <option key={item.code} value={item.code}>{item.name} ({item.code.toUpperCase()})</option>)}
            </select>
            <p id="country-help" className="help">Changing storefront reruns only your last submitted phrase, not unfinished edits.</p>
          </div>
          <form onSubmit={submit} noValidate autoComplete="off">
            <fieldset className="search-modes">
              <legend>Search mode</legend>
              <label><input type="radio" name="mode" value="keyword" checked={mode === "keyword"} onChange={() => changeMode("keyword")} /> Keyword</label>
              <label><input type="radio" name="mode" value="app-name" checked={mode === "app-name"} onChange={() => changeMode("app-name")} /> App name</label>
            </fieldset>
            <label htmlFor="search">Search phrase</label>
            <div className="search-controls">
              <input id="search" name="query" type="search" value={draft} onChange={(event) => setDraft(event.target.value)} placeholder={mode === "keyword" ? "e.g. adhd planner" : "e.g. Tiimo"} autoComplete="off" aria-describedby="search-help" aria-invalid={screen.kind === "error" && screen.code === "VALIDATION_ERROR"} />
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
            {screen.kind === "success" && `${screen.data.results.length} displayed ${mode === "app-name" ? "app candidates" : "search results"} for “${screen.data.query}” in ${screen.submitted.country.name}.`}
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
            <div className="result-heading"><div><p className="eyebrow">{screen.submitted.country.name} · {screen.data.country.toUpperCase()}</p><h2>{`${mode === "app-name" ? "Candidates" : "Matches"} for “${screen.data.query}”`}</h2></div><span className="result-count">{screen.data.results.length} displayed</span></div>
            <p className="result-note">Limited search matches · Up to 50 · Apple’s returned order, not a complete catalog.</p>
            <p className="result-note">Average ratings and rating counts belong to the {screen.submitted.country.name} ({screen.data.country.toUpperCase()}) storefront, not global totals. Ratings are not written reviews.</p>
            {mode === "app-name" && screen.data.results.length > 0 && <p className="candidate-help">Compare names and developers, then confirm the intended app. No candidate is automatically verified, even when only one is returned.</p>}
            <p className="fetch-info">Metadata fetched <time dateTime={screen.data.fetchedAt}>{new Date(screen.data.fetchedAt).toLocaleString()}</time> · {screen.data.cached ? "Cached metadata" : "Fresh from Apple · Not cached"}</p>
            {screen.data.results.length === 0 ? <div className="empty-state"><h3>No matches in this storefront.</h3><p>Apple returned no usable app matches. Try another phrase; no other country was substituted.</p></div> : <ol className="results">
              {screen.data.results.map((app) => <ListingRow key={app.appId} app={app}>
                <button type="button" onClick={(event) => openDetails(app.appId, screen.data.country, event.currentTarget)} aria-label={`Open ${app.name ?? `app ${app.appId}`} by ${app.developer ?? "unavailable developer"} (Apple app ID ${app.appId})`}>{mode === "app-name" ? "Confirm app" : "Open app"}</button>
              </ListingRow>)}
            </ol>}
          </>}
        </section>
        <Settings />
        <footer>Searches stay in this session. Bookmark a detail page to reopen that app and storefront.<br />Apple, the Apple logo, and App Store are trademarks of Apple Inc., registered in the U.S. and other countries.</footer>
      </main>
    </>
  );
}
