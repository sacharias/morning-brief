// Saved queue — a client-only reading list persisted in localStorage.
// Entries are keyed (url, else title) so re-saving an item from a later
// brief replaces the old entry instead of duplicating it.

const STORAGE_KEY = "mb-saved-v1";
const CHANGE_EVENT = "mb-saved-change";

// Snapshot cache so getSaved() is referentially stable between writes —
// required by useSyncExternalStore to avoid render loops.
let cache = null;

function load() {
  try {
    const parsed = JSON.parse(localStorage.getItem(STORAGE_KEY) ?? "[]");
    return Array.isArray(parsed) ? parsed : [];
  } catch {
    return [];
  }
}

export function savedKeyOf(item) {
  return item.url ?? item.title;
}

export function getSaved() {
  if (cache === null) cache = load();
  return cache;
}

export function isSaved(key) {
  return getSaved().some((entry) => entry.key === key);
}

function commit(next) {
  cache = next;
  try {
    localStorage.setItem(STORAGE_KEY, JSON.stringify(next));
  } catch {
    // Storage may be full or unavailable; the in-memory list still works.
  }
  window.dispatchEvent(new Event(CHANGE_EVENT));
}

// Toggle an entry {key, title, body, url, briefDate}; stamps savedAt on save.
// Returns true when the entry is now saved.
export function toggleSaved(entry) {
  const rest = getSaved().filter((e) => e.key !== entry.key);
  const adding = rest.length === getSaved().length;
  commit(adding ? [{ ...entry, savedAt: new Date().toISOString() }, ...rest] : rest);
  return adding;
}

// useSyncExternalStore-compatible: fires on local toggles (custom event)
// and on writes from other tabs (storage event).
export function subscribe(listener) {
  const onStorage = (event) => {
    if (event.key !== null && event.key !== STORAGE_KEY) return;
    cache = null;
    listener();
  };
  window.addEventListener(CHANGE_EVENT, listener);
  window.addEventListener("storage", onStorage);
  return () => {
    window.removeEventListener(CHANGE_EVENT, listener);
    window.removeEventListener("storage", onStorage);
  };
}
