import { useSyncExternalStore } from "react";
import { getSaved, subscribe } from "../lib/saved.js";
import { SaveButton } from "./Section.jsx";

function formatDay(iso) {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

function SavedRow({ entry, index }) {
  // Same content-aware read as the brief rows: X posts lead with the story,
  // everything else with its title.
  const isPost = entry.title?.startsWith("@");
  return (
    <article
      className="mb-rise group relative flex gap-3 px-4 py-3.5 transition-colors duration-150 active:bg-paper"
      style={{ "--i": Math.min(index, 8) }}
    >
      <div className="min-w-0 flex-1">
        {isPost ? (
          <>
            <p className="text-[0.75rem] font-medium text-ink-soft">{entry.title}</p>
            {entry.body && (
              <p className="mt-1 leading-[1.5] text-ink transition-colors duration-150 group-hover:text-accent-deep">
                {entry.body}
              </p>
            )}
          </>
        ) : (
          <>
            <h3 className="font-medium leading-snug break-words text-ink transition-colors duration-150 group-hover:text-accent-deep">
              {entry.title}
            </h3>
            {entry.body && <p className="mt-1 text-sm leading-[1.5] text-ink-soft">{entry.body}</p>}
          </>
        )}
      </div>
      <SaveButton entry={entry} className="-my-2 -me-3 self-start" />
      {entry.url && (
        <a
          className="absolute inset-0"
          href={entry.url}
          target="_blank"
          rel="noreferrer"
          aria-label={isPost ? `${entry.title}: ${entry.body || "open post"}` : entry.title}
        />
      )}
    </article>
  );
}

// The saved queue, grouped by the brief day each item was saved from,
// newest day first. Entries within a day are already newest-saved first.
export default function SavedPage() {
  const entries = useSyncExternalStore(subscribe, getSaved);

  if (!entries.length) {
    return (
      <div className="mt-10 rounded-2xl border border-line bg-surface px-6 py-12 text-center">
        <p className="font-serif text-lg font-semibold">Nothing saved yet</p>
        <p className="mt-1 text-sm text-ink-soft">Tap the bookmark on any item to keep it here.</p>
      </div>
    );
  }

  const byDate = new Map();
  for (const entry of entries) {
    const date = entry.briefDate ?? "";
    if (!byDate.has(date)) byDate.set(date, []);
    byDate.get(date).push(entry);
  }
  const dates = [...byDate.keys()].sort((a, b) => (a < b ? 1 : -1));

  return (
    <>
      {dates.map((date) => (
        <section key={date || "undated"} className="mt-8 first:mt-5">
          <h2 className="mb-3 font-serif text-[0.9375rem] font-semibold text-ink-mid">
            {date ? formatDay(date) : "Saved earlier"}
          </h2>
          <div className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
            {byDate.get(date).map((entry, i) => (
              <SavedRow key={entry.key} entry={entry} index={i} />
            ))}
          </div>
        </section>
      ))}
    </>
  );
}
