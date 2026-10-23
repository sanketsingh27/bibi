"use client";

import { useRef, useState } from "react";
import type { AppDetailsResponse } from "./api";

function Screenshot({ url, index, app }: { url: string; index: number; app: AppDetailsResponse }) {
  const [failed, setFailed] = useState(false);
  return <li>
    {failed ? <p>Screenshot {index + 1} unavailable.</p> : <img src={url} alt={`${app.name ?? `App ${app.appId}`} — App Store screenshot ${index + 1}`} loading="lazy" referrerPolicy="no-referrer" onError={() => setFailed(true)} />}
    <a className="store-badge" href={app.storeUrl!} target="_blank" rel="noopener noreferrer" aria-label={`View original listing for screenshot ${index + 1} (new tab)`}><img src="/download-on-the-app-store.svg" alt="Download on the App Store" width="120" height="40" /></a>
  </li>;
}

export function DetailContent({ app }: { app: AppDetailsResponse }) {
  const tabs = ["Analysis", "Reviews", "Competitors"];
  const [active, setActive] = useState(0);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  return <>
    <dl className="listing-metadata detail-facts">
      <div><dt>Price</dt><dd>{app.formattedPrice ?? "Unavailable"}</dd></div>
      <div><dt>Version</dt><dd>{app.version ?? "Unavailable"}</dd></div>
      <div><dt>First release</dt><dd>{app.releaseDate ? <time dateTime={app.releaseDate}>{new Date(app.releaseDate).toLocaleDateString()}</time> : "Unavailable"}</dd></div>
      <div><dt>Current version released</dt><dd>{app.currentVersionReleaseDate ? <time dateTime={app.currentVersionReleaseDate}>{new Date(app.currentVersionReleaseDate).toLocaleDateString()}</time> : "Unavailable"}</dd></div>
    </dl>
    <section aria-labelledby="description-title"><h2 id="description-title">About this app</h2><p className="listing-text">{app.description ?? "Description unavailable."}</p></section>
    <section aria-labelledby="screenshots-title"><h2 id="screenshots-title">App Store screenshots</h2>
      {app.screenshotUrls.length > 0 && app.storeUrl ? <ul className="screenshots">{app.screenshotUrls.map((url, index) => <Screenshot key={url} url={url} index={index} app={app} />)}</ul> : <p>{app.screenshotUrls.length > 0 ? "Screenshots unavailable without a safe original listing link." : "Screenshots unavailable."}</p>}
    </section>
    <section aria-labelledby="release-title"><h2 id="release-title">Release notes</h2><p className="listing-text">{app.releaseNotes ?? "Release notes unavailable."}</p></section>
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
      {index === 0 && <><p>Analysis unavailable. Review collection and analysis are not available in this version.</p><p>No written-review sample has been collected here. Analysis will require a review sample, an OpenRouter key, a compatible selected model, and local embedding setup.</p></>}
      {index === 1 && <><p>Written reviews unavailable. Review collection is not available in this version.</p><p>The listing rating count above is not a written-review count.</p></>}
      {index === 2 && <><p>Competitor suggestions unavailable. Suggestions and comparison are not available in this version.</p><p>No apps have been classified as competitors.</p></>}
      <p className="help">Changing tabs does not collect reviews or start paid analysis.</p>
    </section>)}
  </>;
}
