import { Fragment, useState } from "react";

const PREVIEW_COUNT = 6;

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

function Item({ item, rank, index = 0 }) {
  // X items carry the story in `body` and only a handle in `title` — read the
  // story first, byline second. Everything else leads with its title.
  const isPost = item.title?.startsWith("@");
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
              {item.isNew && <NewFlag />}
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
              {item.isNew && <NewFlag />}
            </h3>
            {item.body && <p className="mt-1 text-sm leading-[1.5] text-ink-soft">{item.body}</p>}
          </>
        )}
        <MetaLine metrics={item.metrics} tags={item.tags} />
      </div>
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

export default function Section({ section, hideHead = false }) {
  const [expanded, setExpanded] = useState(false);
  const items = section.items ?? [];
  const previewCount = section.previewCount ?? PREVIEW_COUNT;
  const visible = expanded ? items : items.slice(0, previewCount);
  const hidden = items.length - previewCount;

  return (
    <section className="mt-8 first:mt-5" id={section.id}>
      {!hideHead && (
        <SectionHead title={section.title} description={section.description} count={items.length} />
      )}
      <div className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
        {items.length ? (
          <>
            {visible.map((item, i) => (
              <Item
                key={item.url ?? `${section.id}-${i}`}
                item={item}
                rank={i + 1}
                // Rows revealed by "Show all" restart the stagger from zero
                index={i < previewCount ? i : i - previewCount}
              />
            ))}
            {hidden > 0 && (
              <button
                type="button"
                className="w-full cursor-pointer px-4 py-3 text-center text-[0.8125rem] font-medium text-accent transition-colors duration-150 hover:bg-paper/60 active:bg-paper"
                onClick={() => setExpanded((v) => !v)}
              >
                {expanded ? "Show fewer" : `Show all ${items.length}`}
              </button>
            )}
          </>
        ) : (
          <p className="px-4 py-4 text-sm text-ink-soft">
            {section.emptyMessage ?? "Nothing captured today."}
          </p>
        )}
      </div>
    </section>
  );
}
