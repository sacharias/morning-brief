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
    <article className="item">
      <div className="item-head">
        <span className="item-rank">{String(rank).padStart(2, "0")}</span>
        {item.url ? (
          <a className="item-title" href={item.url} target="_blank" rel="noreferrer">
            {item.title}
          </a>
        ) : (
          <span className="item-title">{item.title}</span>
        )}
      </div>
      {item.body && <p className="item-body">{item.body}</p>}
      {(item.metrics?.length || item.tags?.length) > 0 && (
        <div className="item-meta">
          {item.metrics?.map((m) => (
            <span className="chip" key={m.label}>
              <strong>{m.value}</strong> {m.label}
            </span>
          ))}
          {item.tags?.map((t) => (
            <span className="chip chip-tag" key={t}>
              {t}
            </span>
          ))}
        </div>
      )}
    </article>
  );
}

function Section({ section }) {
  return (
    <section className="section" id={section.id}>
      <header className="section-head">
        <h2>{section.title}</h2>
        {section.description && <p>{section.description}</p>}
      </header>
      {section.items?.length ? (
        <div className="item-list">
          {section.items.map((item, i) => (
            <Item key={item.url ?? `${section.id}-${i}`} item={item} rank={i + 1} />
          ))}
        </div>
      ) : (
        <p className="empty-state">{section.emptyMessage ?? "Nothing captured today."}</p>
      )}
    </section>
  );
}

export default function Brief({ brief }) {
  return (
    <>
      <header className="brief-hero">
        <p className="kicker">{formatDate(brief.date)}</p>
        {brief.headline && <h1>{brief.headline}</h1>}
        {brief.executiveSummary?.length > 0 && (
          <ul className="exec-summary">
            {brief.executiveSummary.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        )}
      </header>

      {brief.sections?.map((section) => (
        <Section key={section.id} section={section} />
      ))}

      {brief.followUps?.length > 0 && (
        <section className="section">
          <header className="section-head">
            <h2>Follow-ups</h2>
          </header>
          <ul className="follow-ups">
            {brief.followUps.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}

      {brief.runNotes?.length > 0 && (
        <section className="section">
          <header className="section-head">
            <h2>Run notes</h2>
          </header>
          <ul className="run-notes">
            {brief.runNotes.map((line, i) => (
              <li key={i}>{line}</li>
            ))}
          </ul>
        </section>
      )}
    </>
  );
}
