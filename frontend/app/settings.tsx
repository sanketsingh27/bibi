"use client";

import { useEffect, useState, type FormEvent } from "react";

type Settings = { hasKey: boolean; selectedModelId: null; storeStatus: "available" | "unavailable" };

const messages: Record<string, string> = {
  VALIDATION_ERROR: "Enter a valid OpenRouter key. The key was not saved.",
  CREDENTIAL_STORE_UNAVAILABLE: "macOS Keychain is unavailable or locked. No changes were saved.",
  LOCAL_REQUEST_FORBIDDEN: "This local request was blocked. Open Bibi from its loopback address.",
};

export function Settings() {
  const [settings, setSettings] = useState<Settings | null>(null);
  const [key, setKey] = useState("");
  const [busy, setBusy] = useState(false);
  const [message, setMessage] = useState("Checking secure key status…");

  async function refresh() {
    try {
      const response = await fetch("/api/v1/ai/settings", { cache: "no-store" });
      if (!response.ok) throw new Error();
      const data: Settings = await response.json();
      setSettings(data);
      setMessage(data.storeStatus === "available"
        ? data.hasKey ? "OpenRouter key is saved in macOS Keychain." : "No OpenRouter key is saved."
        : "macOS Keychain is unavailable or locked. No key can be saved.");
    } catch {
      setSettings(null);
      setMessage("Could not read secure key status. Check that the local API is running.");
    }
  }

  useEffect(() => { void refresh(); }, []);

  async function save(event: FormEvent<HTMLFormElement>) {
    event.preventDefault();
    setBusy(true);
    setMessage("Saving to macOS Keychain…");
    try {
      const response = await fetch("/api/v1/ai/settings", {
        method: "PUT",
        headers: { "Content-Type": "application/json" },
        body: JSON.stringify({ apiKey: key }),
      });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setMessage(messages[body?.error?.code] ?? "The key could not be saved.");
      } else {
        setKey("");
        await refresh();
      }
    } catch {
      setMessage("Could not reach the local API. The key was not confirmed saved.");
    } finally {
      setBusy(false);
    }
  }

  async function remove() {
    setBusy(true);
    setMessage("Removing the app's key from macOS Keychain…");
    try {
      const response = await fetch("/api/v1/ai/key", { method: "DELETE" });
      if (!response.ok) {
        const body = await response.json().catch(() => null);
        setMessage(messages[body?.error?.code] ?? "The key could not be removed.");
      } else {
        setKey("");
        await refresh();
      }
    } catch {
      setMessage("Could not reach the local API. The key removal was not confirmed.");
    } finally {
      setBusy(false);
    }
  }

  return <section className="settings-panel" aria-labelledby="settings-heading">
    <p className="eyebrow">Local settings</p>
    <h2 id="settings-heading">OpenRouter key</h2>
    <p className="settings-copy">Stored in this Mac’s Keychain. Bibi never returns or stores the key in browser data. Saving does not make an inference request.</p>
    <p className="settings-status" role="status" aria-live="polite">{message}</p>
    <form onSubmit={save} autoComplete="off">
      <label htmlFor="openrouter-key">{settings?.hasKey ? "Replace key" : "OpenRouter API key"}</label>
      <div className="search-controls">
        <input id="openrouter-key" type="password" value={key} onChange={(event) => setKey(event.target.value)} autoComplete="new-password" spellCheck={false} disabled={busy || settings?.storeStatus === "unavailable"} />
        <button type="submit" disabled={busy || !key || settings?.storeStatus === "unavailable"}>Save key</button>
      </div>
    </form>
    {settings?.hasKey && <button type="button" className="secondary" disabled={busy} onClick={() => void remove()}>Remove key</button>}
    <p className="help">Key status only. Model selection is not available in this Settings slice. No key material is sent to an inference provider while configuring.</p>
  </section>;
}
