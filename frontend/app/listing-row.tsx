"use client";

import { useState, type ReactNode } from "react";
import type { Listing } from "./api";

export function ListingRow({ app, children }: { app: Listing; children?: ReactNode }) {
  const [iconFailed, setIconFailed] = useState(false);
  const [copyState, setCopyState] = useState<"idle" | "pending" | "success" | "error">("idle");
  // Artwork is promotional content: never show it without its original listing badge.
  const showIcon = Boolean(app.iconUrl && app.storeUrl && !iconFailed);

  async function copyId() {
    setCopyState("pending");
    try {
      await navigator.clipboard.writeText(String(app.appId));
      setCopyState("success");
    } catch {
      setCopyState("error");
    }
  }

  return <li>
    <div className="listing-identity">
      <h3>{app.name ?? "App name unavailable"}</h3>
      <p>{app.developer ?? "Developer unavailable"}</p>
      <dl className="listing-metadata">
        <div><dt>Category</dt><dd>{app.category ?? "Unavailable"}</dd></div>
        <div><dt>Average rating</dt><dd>{app.averageRating === null ? "Unavailable" : `${app.averageRating.toLocaleString(undefined, { maximumFractionDigits: 2 })} / 5`}</dd></div>
        <div><dt>Ratings</dt><dd>{app.ratingCount === null ? "Unavailable" : app.ratingCount.toLocaleString()}</dd></div>
      </dl>
      <p className="app-id">Apple app ID <span>{app.appId}</span></p>
      <button type="button" className="secondary copy-id" onClick={() => void copyId()} disabled={copyState === "pending"} aria-label={`Copy Apple app ID ${app.appId}`}>{copyState === "pending" ? "Copying…" : "Copy app ID"}</button>
      <p className={`copy-status${copyState === "error" ? " copy-error" : ""}`} role="status" aria-live="polite" aria-atomic="true">
        {copyState === "success" && `Copied Apple app ID ${app.appId}.`}
        {copyState === "error" && `Could not copy Apple app ID ${app.appId}. Select and copy the number above manually.`}
      </p>
    </div>
    <div className="listing-artwork">
      {children}
      {showIcon ? <img className="app-icon" src={app.iconUrl!} alt={`${app.name ?? `App ${app.appId}`} icon`} width="80" height="80" loading="lazy" referrerPolicy="no-referrer" onError={() => setIconFailed(true)} /> : <span className="icon-unavailable">{app.iconUrl && !app.storeUrl ? "Icon unavailable without a listing link" : "Icon unavailable"}</span>}
      {app.storeUrl ? <a className="store-badge" href={app.storeUrl} target="_blank" rel="noopener noreferrer" aria-label={`Open ${app.name ?? `app ${app.appId}`} on the App Store (new tab)`}><img src="/download-on-the-app-store.svg" alt="Download on the App Store" width="120" height="40" /></a> : <span className="link-unavailable">Listing link unavailable</span>}
    </div>
  </li>;
}
