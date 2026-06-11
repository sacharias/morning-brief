import Section, { SectionHead } from "./Section.jsx";

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

function GroupList({ title, lines, small }) {
  if (!lines?.length) return null;
  return (
    <section className="mt-8">
      <SectionHead title={title} />
      <div className="divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
        {lines.map((line, i) => (
          <p
            key={i}
            className={`mb-rise px-4 py-3 ${small ? "text-[0.8125rem] text-ink-soft" : "text-sm leading-[1.55] text-ink-mid"}`}
            style={{ "--i": Math.min(i, 8) }}
          >
            {line}
          </p>
        ))}
      </div>
    </section>
  );
}

function EndCap({ generatedAt }) {
  return (
    <footer className="mt-14 mb-2 text-center">
      <div className="flex items-center gap-4" aria-hidden="true">
        <span className="h-px flex-1 bg-line" />
        <span className="font-serif text-sm italic text-ink-soft">That’s the brief</span>
        <span className="h-px flex-1 bg-line" />
      </div>
      {generatedAt && (
        <p className="mt-3 text-[0.6875rem] tabular-nums text-ink-soft">
          Generated{" "}
          {new Date(generatedAt).toLocaleString(undefined, {
            dateStyle: "medium",
            timeStyle: "short",
          })}
        </p>
      )}
    </footer>
  );
}

export default function TodayPage({ brief, extraSections }) {
  return (
    <>
      <header className="pt-6 pb-2 md:pt-10">
        <p
          className="mb-2.5 text-xs font-medium tracking-[0.08em] text-accent uppercase mb-rise"
          style={{ "--i": 0 }}
        >
          {formatDate(brief.date)}
        </p>
        {brief.headline && (
          <h1
            className="font-serif text-[clamp(1.65rem,5.5vw,2.35rem)] leading-[1.18] font-semibold tracking-[-0.015em] text-balance mb-rise"
            style={{ "--i": 1 }}
          >
            {brief.headline}
          </h1>
        )}
        {brief.executiveSummary?.length > 0 && (
          <ul className="mt-6 grid gap-3">
            {brief.executiveSummary.map((line, i) => (
              <li
                key={i}
                className="relative pl-5 text-[0.9375rem] leading-[1.55] text-ink-mid mb-rise before:absolute before:top-[0.6em] before:left-0 before:h-[2px] before:w-2.5 before:bg-accent before:content-['']"
                style={{ "--i": 2 + i }}
              >
                {line}
              </li>
            ))}
          </ul>
        )}
      </header>
      {extraSections?.map((section) => (
        <Section key={section.id} section={section} briefDate={brief.date} />
      ))}
      <GroupList title="Follow-ups" lines={brief.followUps} />
      <GroupList title="Run notes" lines={brief.runNotes} small />
      <EndCap generatedAt={brief.generatedAt} />
    </>
  );
}
