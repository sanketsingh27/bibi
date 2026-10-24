import type { AppDetailsResponse } from "./api";

export type SavedReview = {
  reviewId: string;
  appId: number;
  country: string;
  title: string | null;
  text: string;
  stars: number;
  updatedAt: string;
  version: string | null;
  fetchedAt: string;
};

export type SavedSample = {
  id: string;
  appId: number;
  country: string;
  fingerprint: string;
  reviews: SavedReview[];
  pageObservations: { completedPages: number[]; pageGaps: number[]; pagesAttempted: number };
  targetCount: number;
  sourceAvailability: string;
  savedAt: string;
  listing: AppDetailsResponse;
};

type DerivedData = { id: string; appId: number; country: string; fingerprint: string; status: "current" | "stale"; [key: string]: unknown };

function openDatabase() {
  return new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("bibi-research", 1);
    request.onupgradeneeded = () => {
      const db = request.result;
      db.createObjectStore("listings", { keyPath: "id" });
      db.createObjectStore("samples", { keyPath: "id" });
      db.createObjectStore("derived", { keyPath: "id" });
    };
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error("Research storage is blocked"));
  });
}

async function transaction<T>(stores: string[], mode: IDBTransactionMode, work: (tx: IDBTransaction) => IDBRequest<T>) {
  const db = await openDatabase();
  try {
    return await new Promise<T>((resolve, reject) => {
      const tx = db.transaction(stores, mode);
      const request = work(tx);
      let value: T;
      request.onsuccess = () => { value = request.result; };
      tx.oncomplete = () => resolve(value!);
      tx.onerror = () => reject(tx.error ?? request.error);
      tx.onabort = () => reject(tx.error ?? request.error);
    });
  } finally { db.close(); }
}

const scopeId = (appId: number, country: string) => `${appId}:${country}`;

export async function saveListingSnapshot(listing: AppDetailsResponse) {
  return transaction(["listings"], "readwrite", (tx) => tx.objectStore("listings").put({ id: scopeId(listing.appId, listing.country), listing }));
}

export async function loadListingSnapshot(appId: number, country: string): Promise<AppDetailsResponse | undefined> {
  try {
    const saved = await transaction<{ listing: AppDetailsResponse } | undefined>(["listings"], "readonly", (tx) => tx.objectStore("listings").get(scopeId(appId, country)));
    if (saved?.listing) return saved.listing;
  } catch { /* Fall back to snapshots saved by the earlier detail view. */ }

  return loadLegacyListingSnapshot(appId, country);
}

async function loadLegacyListingSnapshot(appId: number, country: string): Promise<AppDetailsResponse | undefined> {
  const name = "bibi-detail-snapshots";
  if (indexedDB.databases && !(await indexedDB.databases()).some((database) => database.name === name)) return undefined;
  return new Promise((resolve, reject) => {
    let created = false;
    const request = indexedDB.open(name);
    request.onupgradeneeded = () => { created = true; };
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      if (created || !db.objectStoreNames.contains("listings")) {
        db.close();
        if (created) indexedDB.deleteDatabase(name);
        resolve(undefined);
        return;
      }
      const tx = db.transaction("listings", "readonly");
      const lookup = tx.objectStore("listings").get(scopeId(appId, country));
      lookup.onsuccess = () => resolve(lookup.result as AppDetailsResponse | undefined);
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
      tx.oncomplete = () => db.close();
    };
  });
}

async function deleteLegacyListingSnapshot(appId: number, country: string): Promise<void> {
  const name = "bibi-detail-snapshots";
  if (indexedDB.databases && !(await indexedDB.databases()).some((database) => database.name === name)) return;
  await new Promise<void>((resolve, reject) => {
    let created = false;
    const request = indexedDB.open(name);
    request.onupgradeneeded = () => { created = true; };
    request.onerror = () => reject(request.error);
    request.onsuccess = () => {
      const db = request.result;
      if (!db.objectStoreNames.contains("listings")) {
        db.close();
        if (created) indexedDB.deleteDatabase(name);
        resolve();
        return;
      }
      const tx = db.transaction("listings", "readwrite");
      tx.objectStore("listings").delete(scopeId(appId, country));
      tx.oncomplete = () => { db.close(); resolve(); };
      tx.onerror = () => { db.close(); reject(tx.error); };
      tx.onabort = () => { db.close(); reject(tx.error); };
    };
  });
}

export async function latestSample(appId: number, country: string): Promise<SavedSample | undefined> {
  const samples = await transaction<SavedSample[]>(["samples"], "readonly", (tx) => tx.objectStore("samples").getAll());
  return samples.filter((sample) => sample.appId === appId && sample.country === country)
    .sort((a, b) => b.savedAt.localeCompare(a.savedAt))[0];
}

export async function listSavedResearch(): Promise<SavedSample[]> {
  const samples = await transaction<SavedSample[]>(["samples"], "readonly", (tx) => tx.objectStore("samples").getAll());
  const latest = new Map<string, SavedSample>();
  for (const sample of samples) {
    const id = scopeId(sample.appId, sample.country);
    if (!latest.has(id) || latest.get(id)!.savedAt < sample.savedAt) latest.set(id, sample);
  }
  return [...latest.values()].sort((a, b) => a.listing.name?.localeCompare(b.listing.name ?? "") ?? 0);
}

export async function fingerprintSample(appId: number, country: string, reviews: SavedReview[]) {
  const canonical = JSON.stringify({
    appId, country,
    reviews: [...reviews].sort((a, b) => a.reviewId.localeCompare(b.reviewId)).map(({ reviewId, appId: id, country: storefront, title, text, stars, updatedAt, version }) => ({
      reviewId, appId: id, country: storefront, title, text, stars, updatedAt, version,
    })),
  });
  const digest = await crypto.subtle.digest("SHA-256", new TextEncoder().encode(canonical));
  return [...new Uint8Array(digest)].map((byte) => byte.toString(16).padStart(2, "0")).join("");
}

export async function saveSample(sample: SavedSample) {
  const db = await openDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(["samples", "derived"], "readwrite");
      const samples = tx.objectStore("samples");
      const derived = tx.objectStore("derived");
      const rows = samples.getAll();
      rows.onsuccess = () => {
        for (const old of rows.result as SavedSample[]) {
          if (old.appId === sample.appId && old.country === sample.country && old.fingerprint === sample.fingerprint) samples.delete(old.id);
        }
        samples.put(sample);
      };
      const derivedRows = derived.getAll();
      derivedRows.onsuccess = () => {
        for (const item of derivedRows.result as DerivedData[]) {
          if (item.appId === sample.appId && item.country === sample.country && item.fingerprint !== sample.fingerprint) {
            derived.put({ ...item, status: "stale" });
          }
        }
      };
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
}

export async function saveDerivedData(item: DerivedData) {
  return transaction(["derived"], "readwrite", (tx) => tx.objectStore("derived").put(item));
}

export async function deleteResearch(appId: number, country: string) {
  await deleteLegacyListingSnapshot(appId, country);
  const db = await openDatabase();
  try {
    await new Promise<void>((resolve, reject) => {
      const tx = db.transaction(["listings", "samples", "derived"], "readwrite");
      tx.objectStore("listings").delete(scopeId(appId, country));
      for (const name of ["samples", "derived"]) {
        const store = tx.objectStore(name);
        const request = store.getAll();
        request.onsuccess = () => {
          for (const item of request.result as Array<{ appId: number; country: string; id: string }>) {
            if (item.appId === appId && item.country === country) store.delete(item.id);
          }
        };
      }
      tx.oncomplete = () => resolve();
      tx.onerror = () => reject(tx.error);
      tx.onabort = () => reject(tx.error);
    });
  } finally { db.close(); }
}
