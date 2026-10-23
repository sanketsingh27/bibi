"use client";

import { useEffect, useRef, useState } from "react";
import type { AppDetailsResponse } from "./api";

function Screenshot({ url, index, app }: { url: string; index: number; app: AppDetailsResponse }) {
  const [failed, setFailed] = useState(false);
  return <li>
    {failed ? <p>Screenshot {index + 1} unavailable.</p> : <img src={url} alt={`${app.name ?? `App ${app.appId}`} — App Store screenshot ${index + 1}`} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} />}
    <a className="store-badge" href={app.storeUrl!} target="_blank" rel="noopener noreferrer" aria-label={`View original listing for screenshot ${index + 1} (new tab)`}><img src="/download-on-the-app-store.svg" alt="Download on the App Store" width="120" height="40" /></a>
  </li>;
}

function ScreenshotCarousel({ app }: { app: AppDetailsResponse }) {
  const track = useRef<HTMLUListElement>(null);
  const [edges, setEdges] = useState({ start: true, end: true });
  function updateEdges() {
    const list = track.current;
    if (list) setEdges({ start: list.scrollLeft <= 5, end: list.scrollLeft + list.clientWidth >= list.scrollWidth - 1 });
  }
  useEffect(() => {
    const list = track.current;
    if (!list) return;
    const observer = new ResizeObserver(updateEdges);
    observer.observe(list);
    updateEdges();
    return () => observer.disconnect();
  }, []);
  function move(direction: number) {
    const list = track.current;
    if (list) list.scrollBy({ left: direction * list.clientWidth * 0.85, behavior: window.matchMedia("(prefers-reduced-motion: reduce)").matches ? "instant" : "smooth" });
  }
  return <section className="screenshot-section" aria-labelledby="screenshots-title" aria-roledescription="carousel">
    <div className="section-heading"><h2 id="screenshots-title">App Store screenshots</h2>
      {app.screenshotUrls.length > 0 && app.storeUrl && <div className="carousel-controls">
        <button type="button" className="secondary" aria-label="Previous screenshots" aria-controls="screenshot-track" disabled={edges.start} onClick={() => move(-1)}>←</button>
        <button type="button" className="secondary" aria-label="Next screenshots" aria-controls="screenshot-track" disabled={edges.end} onClick={() => move(1)}>→</button>
      </div>}
    </div>
    {app.screenshotUrls.length > 0 && app.storeUrl ? <>
      <ul id="screenshot-track" className="screenshots" ref={track} onScroll={updateEdges} tabIndex={0} aria-label="App screenshots. Scroll horizontally or use the arrow keys." onKeyDown={(event) => {
        if (event.target !== event.currentTarget) return;
        if (event.key === "ArrowRight" || event.key === "ArrowLeft") { event.preventDefault(); move(event.key === "ArrowRight" ? 1 : -1); }
        if (event.key === "Home" || event.key === "End") { event.preventDefault(); track.current?.scrollTo({ left: event.key === "Home" ? 0 : track.current.scrollWidth, behavior: "instant" }); }
      }}>{app.screenshotUrls.map((url, index) => <Screenshot key={url} url={url} index={index} app={app} />)}</ul>
      <p className="help">Scroll to explore screenshots from the original App Store listing.</p>
    </> : <p>{app.screenshotUrls.length > 0 ? "Screenshots unavailable without a safe original listing link." : "Screenshots unavailable."}</p>}
  </section>;
}

function Description({ text }: { text: string | null }) {
  const [expanded, setExpanded] = useState(false);
  const [canExpand, setCanExpand] = useState(false);
  const paragraph = useRef<HTMLParagraphElement>(null);
  useEffect(() => {
    const element = paragraph.current;
    if (!element || expanded) return;
    const measure = () => setCanExpand(element.scrollHeight > element.clientHeight + 1);
    const observer = new ResizeObserver(measure);
    observer.observe(element);
    measure();
    return () => observer.disconnect();
  }, [text, expanded]);
  return <section className="description-section" aria-labelledby="description-title">
    <h2 id="description-title">About this app</h2>
    <p ref={paragraph} id="app-description" className={`listing-text${expanded ? "" : " description-preview"}`}>{text ?? "Description unavailable."}</p>
    {(canExpand || expanded) && <button type="button" className="secondary description-toggle" aria-expanded={expanded} aria-controls="app-description" onClick={() => setExpanded(!expanded)}>{expanded ? "Show less" : "Show more"}</button>}
  </section>;
}

export function DetailContent({ app }: { app: AppDetailsResponse }) {
  const tabs = ["Analysis", "Reviews", "Competitors"];
  const [active, setActive] = useState(1);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  return <>
    <ScreenshotCarousel app={app} />
    <Description text={app.description} />
    <div className="research-tabs" role="tablist" aria-label="App research" onKeyDown={(event) => {
      let next: number;
      if (event.key === "ArrowRight") next = (active + 1) % tabs.length;
      else if (event.key === "ArrowLeft") next = (active + tabs.length - 1) % tabs.length;
      else if (event.key === "Home") next = 0;
      else if (event.key === "End") next = tabs.length - 1;
      else return;
      event.preventDefault(); setActive(next); buttons.current[next]?.focus();
    }}>
      {tabs.map((tab, index) => <button key={tab} type="button" role="tab" id={`tab-${index}`} aria-controls={`panel-${index}`} aria-selected={active === index} tabIndex={active === index ? 0 : -1} ref={(element) => { buttons.current[index] = element; }} onClick={() => setActive(index)}>{tab}</button>)}
    </div>
    {tabs.map((tab, index) => <section key={tab} role="tabpanel" id={`panel-${index}`} aria-labelledby={`tab-${index}`} tabIndex={0} hidden={active !== index} className="research-panel">
      <h2>{tab}</h2>
      {index === 0 && <p>Analysis is not available yet. No written reviews have been collected or analyzed for this app.</p>}
      {index === 1 && <ReviewPanel app={app} />}
      {index === 2 && <p>Competitor suggestions and comparison are not available yet. No apps have been classified as competitors.</p>}
    </section>)}
    <section className="additional-details" aria-labelledby="details-title"><h2 id="details-title">Listing details</h2>
    <dl className="listing-metadata detail-facts">
      <div><dt>Version</dt><dd>{app.version ?? "Unavailable"}</dd></div>
      <div><dt>First release</dt><dd>{app.releaseDate ? <time dateTime={app.releaseDate}>{new Date(app.releaseDate).toLocaleDateString()}</time> : "Unavailable"}</dd></div>
      <div><dt>Current version released</dt><dd>{app.currentVersionReleaseDate ? <time dateTime={app.currentVersionReleaseDate}>{new Date(app.currentVersionReleaseDate).toLocaleDateString()}</time> : "Unavailable"}</dd></div>
    </dl>
    </section>
    <section aria-labelledby="release-title"><h2 id="release-title">Release notes</h2><p className="listing-text">{app.releaseNotes ?? "Release notes unavailable."}</p></section>
  </>;
}

type ReviewOperation = {
  operationId: string;
  status: "queued" | "running" | "succeeded" | "partial" | "rate-limited" | "cancelled" | "failed";
  targetCount: 200 | 500;
  resumeAt: string | null;
  progress: { count: number; targetCount: number; pagesAttempted: number; currentPage: number | null; pageGaps: number[]; completedPages: number[] };
  result: null | {
    count: number; targetCount: number; targetReached: boolean; pagesAttempted: number;
    pageGaps: number[]; warnings: string[]; sourceAvailability: "available" | "empty" | "partial" | "unavailable";
    reviews: { reviewId: string; title: string | null; text: string; stars: number; updatedAt: string; version: string | null }[];
  };
  error: { code: string; message: string } | null;
};

function ReviewPanel({ app }: { app: AppDetailsResponse }) {
  const [operation, setOperation] = useState<ReviewOperation | null>(null);
  const [connectionError, setConnectionError] = useState(false);
  const [operationMissing, setOperationMissing] = useState(false);
  const [now, setNow] = useState(Date.now());
  const controller = useRef<AbortController | null>(null);
  async function track(initial: ReviewOperation, signal: AbortSignal) {
    let current = initial;
    sessionStorage.setItem(`bibi.review-operation.${app.appId}.${app.country}`, current.operationId);
    setOperation(current);
    while (["queued", "running"].includes(current.status)) {
      await new Promise<void>((resolve, reject) => {
        const finish = () => { signal.removeEventListener("abort", abort); resolve(); };
        const abort = () => { window.clearTimeout(timer); signal.removeEventListener("abort", abort); reject(new DOMException("Aborted", "AbortError")); };
        const timer = window.setTimeout(finish, 500);
        signal.addEventListener("abort", abort, { once: true });
      });
      const poll = await fetch(`/api/v1/operations/${encodeURIComponent(current.operationId)}`, { cache: "no-store", signal });
      if (!poll.ok) throw new Error("Review operation is no longer available");
      current = await poll.json() as ReviewOperation;
      setOperation(current);
    }
  }
  async function start(targetCount: 200 | 500) {
    controller.current?.abort();
    const activeController = new AbortController();
    controller.current = activeController;
    setConnectionError(false);
    setOperationMissing(false);
    try {
      const response = await fetch(`/api/v1/apps/${app.appId}/review-fetches`, {
        method: "POST", cache: "no-store", signal: activeController.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ requestId: crypto.randomUUID(), country: app.country, targetCount }),
      });
      if (!response.ok) throw new Error("Review collection could not start");
      setOperationMissing(false);
      await track(await response.json() as ReviewOperation, activeController.signal);
    } catch {
      if (!activeController.signal.aborted) setConnectionError(true);
    }
  }
  async function control(action: "cancel" | "resume") {
    if (!operation) return;
    const activeController = new AbortController();
    controller.current?.abort();
    controller.current = activeController;
    setConnectionError(false);
    try {
      const response = await fetch(`/api/v1/operations/${encodeURIComponent(operation.operationId)}/${action}`, {
        method: "POST", cache: "no-store", signal: activeController.signal,
      });
      if (!response.ok) throw new Error("Review operation control failed");
      await track(await response.json() as ReviewOperation, activeController.signal);
    } catch {
      if (!activeController.signal.aborted) setConnectionError(true);
    }
  }
  useEffect(() => {
    const key = `bibi.review-operation.${app.appId}.${app.country}`;
    const savedOperationId = sessionStorage.getItem(key);
    if (!savedOperationId) {
      void start(200);
      return () => controller.current?.abort();
    }
    const activeController = new AbortController();
    controller.current = activeController;
    void (async () => {
      try {
        const response = await fetch(`/api/v1/operations/${encodeURIComponent(savedOperationId)}`, { cache: "no-store", signal: activeController.signal });
        if (response.status === 404) { setOperationMissing(true); return; }
        if (!response.ok) throw new Error("Review operation could not be loaded");
        await track(await response.json() as ReviewOperation, activeController.signal);
      } catch {
        if (!activeController.signal.aborted) setConnectionError(true);
      }
    })();
    return () => controller.current?.abort();
  }, [app.appId, app.country]);
  useEffect(() => {
    if (!operation?.resumeAt || operation.status !== "rate-limited") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [operation?.resumeAt, operation?.status]);

  const result = operation?.result;
  const progress = operation?.progress;
  const resumeReady = !operation?.resumeAt || new Date(operation.resumeAt).getTime() <= now;
  return <div className="review-sample" aria-busy={operation?.status === "queued" || operation?.status === "running"}>
    <p className="result-note">Target: {operation?.targetCount ?? 200} written reviews, with at most 10 pages checked · This exact app · {app.country.toUpperCase()} storefront. Targets are not guarantees.</p>
    <div className="review-progress" role="status" aria-live="polite">
      {connectionError && "Review collection status could not be loaded. The listing is still available."}
      {operationMissing && "The previous collection status was lost after the local API restarted. No new requests were sent; start a new collection explicitly to continue."}
      {!connectionError && !operation && "Starting Apple's public review collection…"}
      {operation?.status === "queued" && "Review collection queued…"}
      {operation?.status === "running" && `Collecting page ${progress?.currentPage ?? (progress?.pagesAttempted ?? 0) + 1} of 10 · ${progress?.count ?? 0} of ${operation.targetCount} written reviews`}
      {operation?.status === "succeeded" && result && `${result.count} written reviews collected · ${result.pagesAttempted} page requests made${result.targetReached ? " · target reached" : " · target not reached"}`}
      {operation?.status === "partial" && result && `${result.count} written reviews collected before collection stopped · partial sample`}
      {operation?.status === "rate-limited" && result && `${result.count} written reviews retained · Apple asked collection to pause${operation.resumeAt ? ` until ${new Date(operation.resumeAt).toLocaleString()}` : ""}.`}
      {operation?.status === "cancelled" && result && `${result.count} written reviews retained · collection cancelled`}
      {operation?.status === "failed" && (operation.error?.message ?? "Apple's review source could not be reached.")}
    </div>
    {progress && <p className="help">Page requests: {progress.pagesAttempted} · Distinct pages completed: {progress.completedPages.length} of 10{progress.pageGaps.length ? ` · Empty or duplicate-only pages: ${progress.pageGaps.join(", ")}` : ""}</p>}
    {operation && ["queued", "running"].includes(operation.status) && <button type="button" className="secondary" onClick={() => void control("cancel")}>Cancel collection</button>}
    {operation && ["partial", "cancelled", "rate-limited"].includes(operation.status) && <button type="button" className="secondary" disabled={!resumeReady} onClick={() => void control("resume")}>Resume collection</button>}
    {operationMissing && <button type="button" className="secondary" onClick={() => void start(200)}>Start a new collection</button>}
    {operation?.status === "failed" && <button type="button" className="secondary" onClick={() => void start(operation.targetCount)}>Retry collection</button>}
    {operation?.status === "succeeded" && operation.targetCount === 200 && (progress?.completedPages.length ?? 10) < 10 && <button type="button" className="secondary" onClick={() => void start(500)}>Expand target to 500</button>}
    {result && <>
      <p className="result-note">Source availability: {result.sourceAvailability}. Page gaps: {result.pageGaps.length ? result.pageGaps.join(", ") : "none observed"}. This sample does not represent every App Store review.</p>
      {result.warnings.map((warning) => <p className="review-warning" key={warning}>{warning}</p>)}
      {result.reviews.length === 0 ? <p>{result.sourceAvailability === "empty" ? "Apple returned no written reviews in the pages checked. This does not mean the app has no App Store reviews." : "No written reviews were available from this source."}</p> : <ol className="review-list">
        {result.reviews.map((review) => <li key={review.reviewId}>
          <div className="review-heading"><strong>{review.title ?? `${review.stars} stars`}</strong><span>{review.stars} / 5 stars</span></div>
          <p>{review.text}</p>
          <p className="help">Updated <time dateTime={review.updatedAt}>{new Date(review.updatedAt).toLocaleDateString()}</time>{review.version ? ` · Version ${review.version}` : ""}</p>
        </li>)}
      </ol>}
    </>}
  </div>;
}
