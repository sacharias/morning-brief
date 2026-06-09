import { useEffect, useState } from "react";
import Brief from "./components/Brief.jsx";
import DayPicker from "./components/DayPicker.jsx";

const DATA_BASE = `${import.meta.env.BASE_URL}data`;

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  return res.json();
}

export default function App() {
  const [index, setIndex] = useState(null);
  const [day, setDay] = useState(null);
  const [brief, setBrief] = useState(null);
  const [error, setError] = useState(null);

  useEffect(() => {
    fetchJson(`${DATA_BASE}/index.json`)
      .then((idx) => {
        setIndex(idx);
        setDay(idx.latest ?? idx.days?.[0] ?? null);
      })
      .catch((err) => setError(err.message));
  }, []);

  useEffect(() => {
    if (!day) return;
    setBrief(null);
    fetchJson(`${DATA_BASE}/${day}.json`)
      .then(setBrief)
      .catch((err) => setError(err.message));
  }, [day]);

  if (error) {
    return (
      <div className="shell state-message">
        <p>Could not load the brief.</p>
        <p className="state-detail">{error}</p>
      </div>
    );
  }

  return (
    <div className="app">
      <header className="masthead">
        <div className="shell masthead-row">
          <span className="masthead-title">Morning Brief</span>
          {index && index.days.length > 1 && (
            <DayPicker days={index.days} selected={day} onSelect={setDay} />
          )}
        </div>
      </header>
      <main className="shell">
        {brief ? (
          <Brief brief={brief} />
        ) : (
          <p className="state-message">Loading…</p>
        )}
      </main>
      <footer className="shell site-footer">
        {brief?.generatedAt && (
          <span>
            Generated{" "}
            {new Date(brief.generatedAt).toLocaleString(undefined, {
              dateStyle: "medium",
              timeStyle: "short",
            })}
          </span>
        )}
      </footer>
    </div>
  );
}
