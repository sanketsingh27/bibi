"use client";

import { useEffect, useRef, useState } from "react";
import type { AppDetailsResponse } from "./api";
import { deleteResearch, fingerprintSample, latestSample, saveSample, type SavedReview, type SavedSample } from "./research-library";

type ReviewOperation = {
  operationId: string;
  status: "queued" | "running" | "succeeded" | "partial" | "rate-limited" | "cancelled" | "failed";
  targetCount: 200 | 500;
  resumeAt: string | null;
  progress: { count: number; targetCount: number; pagesAttempted: number; currentPage: number | null; pageGaps: number[]; completedPages: number[] };
  result: null | {
    count: number; targetCount: number; targetReached: boolean; pagesAttempted: number;
    pageGaps: number[]; warnings: string[]; sourceAvailability: "available" | "empty" | "partial" | "unavailable";
    reviews: SavedReview[];
  };
  error: { code: string; message: string } | null;
};

export function ReviewPanel({ app, savedScope = false }: { app: AppDetailsResponse; savedScope?: boolean }) {
  const [operation, setOperation] = useState<ReviewOperation | null>(null);
  const [sample, setSample] = useState<SavedSample | null>(null);
  const [ready, setReady] = useState(false);
  const [connectionError, setConnectionError] = useState(false);
  const [operationMissing, setOperationMissing] = useState(false);
  const [now, setNow] = useState(Date.now());
  const [storageMessage, setStorageMessage] = useState("");
  const [filter, setFilter] = useState<"all" | 1 | 2 | 3 | 4 | 5>("all");
  const controller = useRef<AbortController | null>(null);

  async function persist(current: ReviewOperation) {
    const result = current.result;
    if (!result || current.status !== "succeeded" || result.reviews.length === 0) {
      if (current.status === "succeeded" && result?.reviews.length === 0) setStorageMessage("Refresh returned no written reviews. The previous saved sample was kept.");
      return;
    }
    try {
      const fingerprint = await fingerprintSample(app.appId, app.country, result.reviews);
      const saved: SavedSample = {
        id: `${app.appId}:${app.country}:${fingerprint}`, appId: app.appId, country: app.country,
        fingerprint, reviews: result.reviews, targetCount: current.targetCount,
        pageObservations: { completedPages: current.progress.completedPages, pageGaps: result.pageGaps, pagesAttempted: result.pagesAttempted },
        sourceAvailability: result.sourceAvailability, savedAt: new Date().toISOString(), listing: app,
      };
      await saveSample(saved);
      setSample(saved);
      setStorageMessage("Research saved on this device.");
      window.dispatchEvent(new Event("bibi:saved-research-changed"));
    } catch {
      setStorageMessage(`Not saved: this device could not store the review sample. The new result is temporary.${sample ? " Showing the previous saved sample." : ""}`);
    }
  }

  async function track(initial: ReviewOperation, signal: AbortSignal) {
    let current = initial;
    setOperation(current);
    try { sessionStorage.setItem(`bibi.review-operation.${app.appId}.${app.country}`, current.operationId); } catch { /* Session recovery is best effort. */ }
    while (["queued", "running"].includes(current.status)) {
      await new Promise<void>((resolve, reject) => {
        const finish = () => { signal.removeEventListener("abort", abort); resolve(); };
        const abort = () => { window.clearTimeout(timer); signal.removeEventListener("abort", abort); reject(new DOMException("Aborted", "AbortError")); };
        const timer = window.setTimeout(finish, 500);
        signal.addEventListener("abort", abort, { once: true });
      });
      const response = await fetch(`/api/v1/operations/${encodeURIComponent(current.operationId)}`, { cache: "no-store", signal });
      if (!response.ok) throw new Error("Review operation could not be loaded");
      current = await response.json() as ReviewOperation;
      setOperation(current);
    }
    await persist(current);
  }

  async function start(targetCount: 200 | 500, refresh = false) {
    const activeController = new AbortController();
    controller.current?.abort();
    controller.current = activeController;
    setConnectionError(false);
    setOperationMissing(false);
    setStorageMessage("");
    try {
      const response = await fetch(`/api/v1/apps/${app.appId}/review-fetches`, {
        method: "POST", cache: "no-store", signal: activeController.signal,
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({
          requestId: crypto.randomUUID(), country: app.country, targetCount, refresh,
          ...(sample ? { existingSample: {
            appId: sample.appId, country: sample.country, reviews: sample.reviews,
            fingerprint: sample.fingerprint, pageObservations: sample.pageObservations,
          } } : {}),
        }),
      });
      if (!response.ok) throw new Error("Review collection could not start");
      setOperationMissing(false);
      await track(await response.json() as ReviewOperation, activeController.signal);
    } catch { if (!activeController.signal.aborted) setConnectionError(true); }
  }

  async function control(action: "cancel" | "resume") {
    if (!operation) return;
    controller.current?.abort();
    const activeController = new AbortController();
    controller.current = activeController;
    setConnectionError(false);
    try {
      const response = await fetch(`/api/v1/operations/${encodeURIComponent(operation.operationId)}/${action}`, {
        method: "POST", cache: "no-store", signal: activeController.signal,
      });
      if (!response.ok) throw new Error("Review operation control failed");
      await track(await response.json() as ReviewOperation, activeController.signal);
    } catch { if (!activeController.signal.aborted) setConnectionError(true); }
  }

  useEffect(() => {
    let active = true;
    const operationKey = `bibi.review-operation.${app.appId}.${app.country}`;
    void latestSample(app.appId, app.country).then(async (saved) => {
      if (!active) return;
      setSample(saved ?? null);
      setReady(true);
      let savedOperationId: string | null = null;
      try { savedOperationId = sessionStorage.getItem(operationKey); } catch { /* Session recovery is best effort. */ }
      if (savedOperationId) {
        const activeController = new AbortController();
        controller.current = activeController;
        try {
          const response = await fetch(`/api/v1/operations/${encodeURIComponent(savedOperationId)}`, { cache: "no-store", signal: activeController.signal });
          if (response.status === 404) { if (active) setOperationMissing(true); return; }
          if (!response.ok) throw new Error("Review operation could not be loaded");
          await track(await response.json() as ReviewOperation, activeController.signal);
        } catch { if (active && !activeController.signal.aborted) setConnectionError(true); }
      } else if (!saved && !savedScope) void start(200);
    }).catch(() => { if (active) { setStorageMessage("Local research storage is unavailable."); setReady(true); } });
    return () => { active = false; controller.current?.abort(); };
  }, [app.appId, app.country, savedScope]);

  useEffect(() => {
    if (!operation?.resumeAt || operation.status !== "rate-limited") return;
    const timer = window.setInterval(() => setNow(Date.now()), 1000);
    return () => window.clearInterval(timer);
  }, [operation?.resumeAt, operation?.status]);

  async function removeSaved() {
    try {
      await deleteResearch(app.appId, app.country);
      try { sessionStorage.removeItem(`bibi.review-operation.${app.appId}.${app.country}`); } catch { /* Session recovery is best effort. */ }
      setSample(null);
      setOperation(null);
      setStorageMessage("Saved research deleted from this device.");
      window.dispatchEvent(new Event("bibi:saved-research-changed"));
    } catch { setStorageMessage("Could not delete saved research from this device."); }
  }

  const result = operation?.result;
  const storageFailed = storageMessage.startsWith("Not saved:");
  const keepSavedSampleVisible = Boolean(sample) && (storageFailed || operation?.status !== "succeeded");
  const temporaryResult = !keepSavedSampleVisible && Boolean(result?.reviews.length) && (!sample || operation?.status !== "succeeded");
  const displayed = keepSavedSampleVisible ? sample!.reviews : result?.reviews?.length ? result.reviews : sample?.reviews ?? [];
  const filtered = displayed.filter((review) => filter === "all" || review.stars === filter);
  const busy = operation?.status === "queued" || operation?.status === "running";
  const resumeReady = !operation?.resumeAt || Date.parse(operation.resumeAt) <= now;
  return <div className="review-sample" aria-busy={busy}>
    <p className="result-note">{sample ? `${sample.reviews.length} saved reviews · ${sample.country.toUpperCase()} storefront` : temporaryResult ? `${displayed.length} temporary reviews · not saved · ${app.country.toUpperCase()} storefront` : `Target: ${operation?.targetCount ?? 200} written reviews · ${app.country.toUpperCase()} storefront`}. Counts describe this sample, not every App Store review.</p>
    {!ready && <p role="status">Loading saved research…</p>}
    <div className="review-progress" role="status" aria-live="polite">
      {connectionError && "Review collection could not complete. Any previous saved sample was kept."}
      {operationMissing && "The previous collection status was lost after the local API restarted. No new requests were sent; start a new collection explicitly to continue."}
      {!connectionError && !operation && !sample && ready && (savedScope ? "No saved review sample for this app and storefront." : "Starting review collection…")}
      {operation?.status === "queued" && "Review collection queued…"}
      {operation?.status === "running" && `Collecting page ${operation.progress.currentPage ?? operation.progress.pagesAttempted + 1} of 10 · ${operation.progress.count} of ${operation.targetCount} reviews`}
      {operation?.status === "succeeded" && result && `${result.count} reviews collected${result.targetReached ? " · target reached" : " · target not reached"}`}
      {operation?.status === "partial" && "Collection stopped early. Any previous saved research was kept."}
      {operation?.status === "rate-limited" && "Apple paused this collection. Any previous saved research was kept."}
      {operation?.status === "cancelled" && "Collection cancelled. Any previous saved research was kept."}
      {operation?.status === "failed" && (operation.error?.message ?? "Review collection failed. Any previous saved research was kept.")}
    </div>
    {operation?.progress && <p className="help">Page requests: {operation.progress.pagesAttempted} · Completed pages: {operation.progress.completedPages.join(", ") || "none"} · Empty pages: {operation.progress.pageGaps.join(", ") || "none"}</p>}
    {result && <>
      <p className="result-note">Source availability: {result.sourceAvailability}. Page gaps: {result.pageGaps.length ? result.pageGaps.join(", ") : "none observed"}. This sample does not represent every App Store review.</p>
      {result.warnings.map((warning) => <p className="review-warning" key={warning}>{warning}</p>)}
      {result.reviews.length === 0 && operation?.status === "succeeded" && <p>Apple returned no written reviews in the pages checked. This does not mean the app has no App Store reviews.</p>}
    </>}
    <div className="research-actions">
      {busy && <button type="button" className="secondary" onClick={() => void control("cancel")}>Cancel collection</button>}
      {operation && ["partial", "cancelled", "rate-limited"].includes(operation.status) && <button type="button" className="secondary" disabled={!resumeReady} onClick={() => void control("resume")}>Resume collection{!resumeReady && operation.resumeAt ? ` · available in ${Math.ceil((Date.parse(operation.resumeAt) - now) / 1000)}s` : ""}</button>}
      {operationMissing && <button type="button" className="secondary" onClick={() => void start(sample?.targetCount === 500 ? 500 : 200)}>Start a new collection</button>}
      {operation?.status === "failed" && <button type="button" className="secondary" onClick={() => void start(operation.targetCount, true)}>Retry collection</button>}
      {!busy && <button type="button" className="secondary" onClick={() => void start(sample?.targetCount === 500 ? 500 : 200, true)}>Refresh reviews</button>}
      {!busy && sample && sample.targetCount === 200 && sample.pageObservations.completedPages.length < 10 && <button type="button" className="secondary" onClick={() => void start(500)}>Fetch more reviews (up to 500)</button>}
      {!busy && sample && <button type="button" className="secondary" onClick={() => void removeSaved()}>Delete this saved research</button>}
    </div>
    {storageMessage && <p role="status" className="fetch-info">{storageMessage}</p>}
    {displayed.length > 0 && <>
      <label className="review-filter" htmlFor="review-star-filter">{temporaryResult ? "Filter temporary result" : "Filter saved sample"}
        <select id="review-star-filter" value={filter} onChange={(event) => setFilter(event.target.value === "all" ? "all" : Number(event.target.value) as 1 | 2 | 3 | 4 | 5)}>
          <option value="all">All stars</option>{[1, 2, 3, 4, 5].map((stars) => <option value={stars} key={stars}>{stars} stars</option>)}
        </select>
      </label>
      <p className="help">Showing {filtered.length} of {displayed.length} {temporaryResult ? "temporary" : "saved"} reviews.</p>
      {filtered.length ? <ol className="review-list">{filtered.map((review) => <li key={review.reviewId}>
        <div className="review-heading"><strong>{review.title ?? `${review.stars} stars`}</strong><span>{review.stars} / 5 stars</span></div>
        <p>{review.text}</p><p className="help">Updated <time dateTime={review.updatedAt}>{new Date(review.updatedAt).toLocaleDateString()}</time>{review.version ? ` · Version ${review.version}` : ""}</p>
      </li>)}</ol> : <p>No saved reviews match this star filter.</p>}
    </>}
  </div>;
}
