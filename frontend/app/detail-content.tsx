"use client";

import { useEffect, useRef, useState } from "react";
import type { AppDetailsResponse } from "./api";
import { ReviewPanel } from "./review-panel";

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

export function DetailContent({ app, savedScope = false }: { app: AppDetailsResponse; savedScope?: boolean }) {
  const tabs = ["Analysis", "Reviews", "Competitors"];
  const [active, setActive] = useState(1);
  const buttons = useRef<(HTMLButtonElement | null)[]>([]);
  return <>
    {!savedScope && <ScreenshotCarousel app={app} />}
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
      {index === 1 && <ReviewPanel app={app} savedScope={savedScope} />}
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
