import { Fragment, useState, useSyncExternalStore } from "react";
import { isSaved, savedKeyOf, subscribe, toggleSaved } from "../lib/saved.js";

// "101,500" → "101.5K". Only pure comma-grouped numbers are compacted;
// labeled values ("2,535 stars today", "24.0x", "Python") pass through.
function compact(value) {
  const raw = String(value).trim();
  if (!/^[\d,]+$/.test(raw)) return value;
  const n = Number(raw.replace(/,/g, ""));
  if (!Number.isFinite(n) || n < 10_000) return value;
  if (n >= 1_000_000) return `${(n / 1_000_000).toFixed(1).replace(/\.0$/, "")}M`;
  if (n >= 100_000) return `${Math.round(n / 1000)}K`;
  return `${(n / 1000).toFixed(1).replace(/\.0$/, "")}K`;
}

function metricText(m) {
  if (m.label === "language") return String(m.value);
  // Sources sometimes bake the label into the value ("2,535 stars today")
  if (String(m.value).toLowerCase().includes(m.label.toLowerCase())) return String(m.value);
  return `${compact(m.value)} ${m.label}`;
}

function MetaLine({ metrics = [], tags = [] }) {
  const parts = [
    ...metrics.slice(0, 3).map((m) => ({ key: `m-${m.label}`, text: metricText(m), accent: false })),
    ...tags.map((t) => ({ key: `t-${t}`, text: t, accent: true })),
  ];
  if (!parts.length) return null;
  return (
    <p className="mt-2 text-[0.75rem] leading-relaxed text-ink-soft tabular-nums">
      {parts.map((p, i) => (
        <Fragment key={p.key}>
          {i > 0 && <span aria-hidden="true"> · </span>}
          <span className={`whitespace-nowrap ${p.accent ? "font-medium text-accent" : ""}`}>{p.text}</span>
        </Fragment>
      ))}
    </p>
  );
}

function NewFlag() {
  return (
    <span className="ms-2 inline-flex -translate-y-px items-center gap-1 align-middle text-[0.625rem] font-semibold tracking-[0.08em] uppercase text-accent">
      <span aria-hidden="true" className="size-1 rounded-full bg-accent" />
      New
    </span>
  );
}

// Continuity flag for stories that span briefs: "Day 3" = seen on two
// earlier days. Replaces the New flag — an item is either new or developing.
function DayFlag({ count }) {
  return (
    <span
      className="ms-2 inline-flex -translate-y-px items-center gap-1 align-middle text-[0.625rem] font-semibold tracking-[0.08em] uppercase text-accent"
      aria-label={`Appeared in ${count} briefs`}
    >
      <span aria-hidden="true" className="size-1 rounded-full bg-accent" />
      Day {count}
    </span>
  );
}

export function BookmarkIcon({ filled = false, className = "" }) {
  return (
    <svg
      viewBox="0 0 24 24"
      fill={filled ? "currentColor" : "none"}
      stroke="currentColor"
      strokeWidth="1.8"
      strokeLinecap="round"
      strokeLinejoin="round"
      className={className}
      aria-hidden="true"
    >
      <path d="M7.5 4.5h9a1 1 0 0 1 1 1V20l-5.5-3.8L6.5 20V5.5a1 1 0 0 1 1-1z" />
    </svg>
  );
}

// Quiet save affordance: ink-soft outline until saved, filled accent after.
// 44px hit box, positioned above the row's stretched link so a tap saves
// instead of navigating. The pop animation runs only on a user save (not on
// mount of already-saved rows); reduced-motion turns it off in CSS.
export function SaveButton({ entry, className = "" }) {
  const saved = useSyncExternalStore(subscribe, () => isSaved(entry.key));
  const [pop, setPop] = useState(false);
  return (
    <button
      type="button"
      aria-pressed={saved}
      aria-label={saved ? "Remove from saved" : "Save for later"}
      className={`relative z-10 flex size-11 shrink-0 cursor-pointer items-center justify-center transition-colors duration-150 ${
        saved ? "text-accent" : "text-ink-soft hover:text-ink"
      } ${className}`}
      onClick={() => {
        if (toggleSaved(entry)) setPop(true);
      }}
      onAnimationEnd={() => setPop(false)}
    >
      <BookmarkIcon
        filled={saved}
        className={`size-[18px] ${pop ? "mb-save-pop" : ""}`}
      />
    </button>
  );
}

function Item({ item, rank, index = 0, briefDate }) {
  // X items carry the story in `body` and only a handle in `title` — read the
  // story first, byline second. Everything else leads with its title.
  const isPost = item.title?.startsWith("@");
  // A developing story outranks a New flag: an item is never both.
  const briefCount = (item.previously?.length ?? 0) + 1;
  const flag = briefCount > 1 ? <DayFlag count={briefCount} /> : item.isNew ? <NewFlag /> : null;
  return (
    <article
      className="mb-rise group relative flex gap-3 px-4 py-3.5 transition-colors duration-150 active:bg-paper"
      style={{ "--i": Math.min(index, 8) }}
    >
      <span className="w-5 shrink-0 pt-px text-right font-serif text-[0.875rem] italic leading-[1.5] text-ink-soft">
        {rank}
      </span>
      <div className="min-w-0 flex-1">
        {isPost ? (
          <>
            <p className="text-[0.75rem] font-medium text-ink-soft">
              {item.title}
              {flag}
            </p>
            {item.body && (
              <p className="mt-1 leading-[1.5] text-ink transition-colors duration-150 group-hover:text-accent-deep">
                {item.body}
              </p>
            )}
          </>
        ) : (
          <>
            <h3 className="font-medium leading-snug break-words text-ink transition-colors duration-150 group-hover:text-accent-deep">
              {item.title}
              {flag}
            </h3>
            {item.body && <p className="mt-1 text-sm leading-[1.5] text-ink-soft">{item.body}</p>}
          </>
        )}
        <MetaLine metrics={item.metrics} tags={item.tags} />
      </div>
      <SaveButton
        entry={{
          key: savedKeyOf(item),
          title: item.title,
          body: item.body ?? "",
          url: item.url ?? "",
          briefDate,
        }}
        className="-my-2 -me-3 self-start"
      />
      {item.url && (
        <a
          className="absolute inset-0"
          href={item.url}
          target="_blank"
          rel="noreferrer"
          aria-label={isPost ? `${item.title}: ${item.body ?? "open post"}` : item.title}
        />
      )}
    </article>
  );
}

export function SectionHead({ title, description, count }) {
  return (
    <header className="mb-3">
      <div className="flex items-baseline justify-between gap-3">
        <h2 className="font-serif text-xl font-semibold">{title}</h2>
        {count > 0 && (
          <span className="text-xs tabular-nums text-ink-soft" aria-label={`${count} items`}>
            {count}
          </span>
        )}
      </div>
      {description && <p className="mt-0.5 text-[0.8125rem] text-ink-soft">{description}</p>}
    </header>
  );
}

export default function Section({ section, hideHead = false, briefDate }) {
  const items = section.items ?? [];

  return (
    <section className="mt-8 first:mt-5" id={section.id}>
      {!hideHead && (
        <SectionHead title={section.title} description={section.description} count={items.length} />
      )}
      <div className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
        {items.length ? (
          items.map((item, i) => (
            <Item
              key={item.url ?? `${section.id}-${i}`}
              item={item}
              rank={i + 1}
              briefDate={briefDate}
              index={i}
            />
          ))
        ) : (
          <p className="px-4 py-4 text-sm text-ink-soft">
            {section.emptyMessage ?? "Nothing captured today."}
          </p>
        )}
      </div>
    </section>
  );
}
