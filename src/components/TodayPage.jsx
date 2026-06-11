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

function ProseList({ title, lines, small }) {
  if (!lines?.length) return null;
  return (
    <section className="mt-7">
      <SectionHead title={title} />
      <ul className="grid gap-2">
        {lines.map((line, i) => (
          <li
            key={i}
            className={`mb-rise rounded-xl border border-line bg-surface px-4 py-3 text-ink-soft ${small ? "text-[0.8125rem]" : "text-sm"}`}
            style={{ "--i": Math.min(i, 8) }}
          >
            {line}
          </li>
        ))}
      </ul>
    </section>
  );
}

export default function TodayPage({ brief, extraSections }) {
  return (
    <>
      <header className="pt-5 pb-1 md:pt-8">
        <p className="mb-2 text-xs font-medium tracking-[0.08em] text-accent uppercase mb-rise" style={{ "--i": 0 }}>
          {formatDate(brief.date)}
        </p>
        {brief.headline && (
          <h1
            className="font-serif text-[clamp(1.6rem,5.5vw,2.25rem)] leading-[1.2] font-semibold tracking-tight text-balance mb-rise"
            style={{ "--i": 1 }}
          >
            {brief.headline}
          </h1>
        )}
        {brief.executiveSummary?.length > 0 && (
          <ul className="mt-5 grid gap-2.5">
            {brief.executiveSummary.map((line, i) => (
              <li
                key={i}
                className="relative pl-[1.1rem] text-[0.9375rem] text-ink-soft mb-rise before:absolute before:top-[0.55em] before:left-0 before:h-[2px] before:w-[0.45rem] before:bg-accent before:content-['']"
                style={{ "--i": 2 + i }}
              >
                {line}
              </li>
            ))}
          </ul>
        )}
      </header>
      {extraSections?.map((section) => (
        <Section key={section.id} section={section} />
      ))}
      <ProseList title="Follow-ups" lines={brief.followUps} />
      <ProseList title="Run notes" lines={brief.runNotes} small />
    </>
  );
}
