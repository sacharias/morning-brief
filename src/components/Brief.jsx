import { useState } from "react";

const PREVIEW_COUNT = 6;

function formatDate(iso) {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString("en-US", {
    weekday: "long",
    year: "numeric",
    month: "long",
    day: "numeric",
  });
}

function Item({ item, rank }) {
  return (
    <article className="rounded-xl border border-line bg-surface px-4 py-3.5">
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

function SectionHead({ title, description }) {
  return (
    <header className="mb-3.5 flex items-baseline gap-3 border-b border-line pb-2">
      <h2 className="font-serif text-xl font-semibold">{title}</h2>
      {description && <p className="text-[0.8125rem] text-ink-soft">{description}</p>}
    </header>
  );
}

function Section({ section }) {
  const [expanded, setExpanded] = useState(false);
  const items = section.items ?? [];
  const previewCount = section.previewCount ?? PREVIEW_COUNT;
  const visible = expanded ? items : items.slice(0, previewCount);
  const hidden = items.length - previewCount;

  return (
    <section className="mt-9" id={section.id}>
      <SectionHead title={section.title} description={section.description} />
      {items.length ? (
        <div className="grid gap-2.5">
          {visible.map((item, i) => (
            <Item key={item.url ?? `${section.id}-${i}`} item={item} rank={i + 1} />
          ))}
          {hidden > 0 && (
            <button
              type="button"
              className="w-full cursor-pointer rounded-xl border border-dashed border-line py-2 text-[0.8125rem] font-medium text-ink-soft transition-colors hover:border-accent/40 hover:text-accent"
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

function ProseList({ title, lines, small }) {
  if (!lines?.length) return null;
  return (
    <section className="mt-9">
      <SectionHead title={title} />
      <ul className="grid gap-2">
        {lines.map((line, i) => (
          <li
            key={i}
            className={`rounded-xl border border-line bg-surface px-4 py-3 text-ink-soft ${small ? "text-[0.8125rem]" : "text-sm"}`}
          >
            {line}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function Brief({ brief }) {
  return (
    <>
      <header className="pt-7 pb-2 md:pt-10 md:pb-3">
        <p className="mb-2 text-xs font-medium tracking-[0.08em] text-accent uppercase">
          {formatDate(brief.date)}
        </p>
        {brief.headline && (
          <h1 className="font-serif text-[clamp(1.6rem,5.5vw,2.25rem)] leading-[1.2] font-semibold tracking-tight text-balance">
            {brief.headline}
          </h1>
        )}
        {brief.executiveSummary?.length > 0 && (
          <ul className="mt-5 grid gap-2.5">
            {brief.executiveSummary.map((line, i) => (
              <li
                key={i}
                className="relative pl-[1.1rem] text-[0.9375rem] text-ink-soft before:absolute before:top-[0.55em] before:left-0 before:h-[2px] before:w-[0.45rem] before:bg-accent before:content-['']"
              >
                {line}
              </li>
            ))}
          </ul>
        )}
      </header>

      {brief.sections?.map((section) => (
        <Section key={section.id} section={section} />
      ))}

      <ProseList title="Follow-ups" lines={brief.followUps} />
      <ProseList title="Run notes" lines={brief.runNotes} small />
    </>
  );
}
