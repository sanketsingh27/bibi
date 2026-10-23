import type { AppDetailsResponse } from "./api";

function text(value: unknown): string | null {
  return typeof value === "string" && value.trim() ? value : null;
}
function date(value: unknown): string | null {
  return typeof value === "string" && /^\d{4}-\d{2}-\d{2}T/.test(value) && Number.isFinite(Date.parse(value)) ? value : null;
}
function url(value: unknown, listing = false): string | null {
  if (typeof value !== "string" || /[\s\u0000-\u001f\\]/u.test(value)) return null;
  try {
    const parsed = new URL(value);
    return parsed.protocol === "https:" && !parsed.username && !parsed.password && !parsed.port
      && (!listing || ["apps.apple.com", "itunes.apple.com"].includes(parsed.hostname)) ? value : null;
  } catch { return null; }
}

// Both the API response and IndexedDB are untrusted. Reconstruct known fields only.
export function validatedDetails(value: unknown, appId: number, country: string): AppDetailsResponse | null {
  if (!value || typeof value !== "object") return null;
  const data = value as Record<string, unknown>;
  if (!Number.isSafeInteger(appId) || appId <= 0 || data.appId !== appId || data.country !== country
      || !/^[a-z]{2}$/.test(country) || !date(data.fetchedAt) || typeof data.cached !== "boolean") return null;
  return {
    appId, country, fetchedAt: date(data.fetchedAt)!, cached: data.cached,
    name: text(data.name), developer: text(data.developer), category: text(data.category),
    iconUrl: url(data.iconUrl), storeUrl: url(data.storeUrl, true),
    averageRating: typeof data.averageRating === "number" && data.averageRating >= 0 && data.averageRating <= 5 ? data.averageRating : null,
    ratingCount: typeof data.ratingCount === "number" && Number.isSafeInteger(data.ratingCount) && data.ratingCount >= 0 ? data.ratingCount : null,
    description: text(data.description), version: text(data.version), formattedPrice: text(data.formattedPrice),
    releaseDate: date(data.releaseDate), currentVersionReleaseDate: date(data.currentVersionReleaseDate), releaseNotes: text(data.releaseNotes),
    screenshotUrls: Array.isArray(data.screenshotUrls) ? [...new Set(data.screenshotUrls.map((value) => url(value)).filter((value): value is string => value !== null))] : [],
  };
}

// Persist metadata/URLs only, never artwork files or credentials.
export async function detailSnapshot(appId: number, country: string, data?: AppDetailsResponse): Promise<unknown> {
  const database = await new Promise<IDBDatabase>((resolve, reject) => {
    const request = indexedDB.open("bibi-detail-snapshots", 1);
    request.onupgradeneeded = () => request.result.createObjectStore("listings");
    request.onsuccess = () => resolve(request.result);
    request.onerror = () => reject(request.error);
    request.onblocked = () => reject(new Error("Snapshot storage blocked"));
  });
  try {
    return await new Promise((resolve, reject) => {
      const transaction = database.transaction("listings", data ? "readwrite" : "readonly");
      const store = transaction.objectStore("listings");
      const request = data ? store.put(data, `${appId}:${country}`) : store.get(`${appId}:${country}`);
      transaction.oncomplete = () => resolve(request.result);
      transaction.onerror = () => reject(transaction.error);
      transaction.onabort = () => reject(transaction.error);
    });
  } finally { database.close(); }
}
