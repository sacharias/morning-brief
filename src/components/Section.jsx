import { useState } from "react";

const PREVIEW_COUNT = 6;

function Item({ item, rank }) {
  return (
    <article className="rounded-xl border border-line bg-surface px-4 py-3.5 transition-transform active:scale-[0.985]">
      <div className="flex min-w-0 items-baseline gap-2.5">
        <span className="shrink-0 text-[0.7rem] font-medium tabular-nums text-ink-soft">
          {String(rank).padStart(2, "0")}
        </span>
        {item.url ? (
          <a
            className="font-medium break-words underline-offset-[3px] hover:text-accent hover:underline"
            href={item.url}
            target="_blank"
            rel="noreferrer"
          >
            {item.title}
          </a>
        ) : (
          <span className="font-medium break-words">{item.title}</span>
        )}
        {item.isNew && (
          <span className="shrink-0 self-center rounded-full border border-accent/30 bg-accent/10 px-1.5 py-px text-[0.6rem] font-semibold uppercase tracking-wide text-accent">
            new
          </span>
        )}
      </div>
      {item.body && <p className="mt-2 text-sm text-ink-soft">{item.body}</p>}
      {(item.metrics?.length || item.tags?.length) > 0 && (
        <div className="mt-2.5 flex flex-wrap gap-1.5">
          {item.metrics?.map((m) => (
            <span
              className="inline-flex items-baseline gap-1 rounded-full border border-line bg-paper px-2 py-0.5 text-[0.7rem] text-ink-soft"
              key={`${m.label}-${m.value}`}
            >
              <strong className="font-semibold text-ink">{m.value}</strong> {m.label}
            </span>
          ))}
          {item.tags?.map((t) => (
            <span
              className="inline-flex items-baseline rounded-full border border-accent/25 bg-accent/10 px-2 py-0.5 text-[0.7rem] text-accent"
              key={t}
            >
              {t}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}

export function SectionHead({ title, description }) {
  return (
    <header className="mb-3.5 border-b border-line pb-2">
      <h2 className="font-serif text-xl font-semibold">{title}</h2>
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
    <section className="mt-7 first:mt-5" id={section.id}>
      {!hideHead && <SectionHead title={section.title} description={section.description} />}
      {items.length ? (
        <div className="grid gap-2.5">
          {visible.map((item, i) => (
            <Item key={item.url ?? `${section.id}-${i}`} item={item} rank={i + 1} />
          ))}
          {hidden > 0 && (
            <button
              type="button"
              className="w-full cursor-pointer rounded-xl border border-dashed border-line py-2.5 text-[0.8125rem] font-medium text-ink-soft transition-all hover:border-accent/40 hover:text-accent active:scale-[0.985]"
              onClick={() => setExpanded((v) => !v)}
            >
              {expanded ? "Show fewer" : `Show all ${items.length}`}
            </button>
          )}
        </div>
      ) : (
        <p className="rounded-xl border border-line bg-surface px-4 py-3 text-sm text-ink-soft">
          {section.emptyMessage ?? "Nothing captured today."}
        </p>
      )}
    </section>
  );
}
