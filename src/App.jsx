import { useEffect, useState } from "react";
import Brief from "./components/Brief.jsx";
import DayPicker from "./components/DayPicker.jsx";

const DATA_BASE = `${import.meta.env.BASE_URL}data`;

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  return res.json();
}

const SHELL = "mx-auto w-full max-w-[680px] px-5";

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
      <div className={`${SHELL} py-12 text-center text-ink-soft`}>
        <p>Could not load the brief.</p>
        <p className="text-[0.8125rem]">{error}</p>
      </div>
    );
  }

  return (
    <div>
      <header className="sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur-sm">
        <div className={`${SHELL} flex items-center justify-between gap-4 py-3`}>
          <span className="font-serif text-lg font-semibold">Morning Brief</span>
          {index && index.days.length > 1 && (
            <DayPicker days={index.days} selected={day} onSelect={setDay} />
          )}
        </div>
      </header>
      <main className={SHELL}>
        {brief ? (
          <Brief brief={brief} />
        ) : (
          <p className="py-12 text-center text-ink-soft">Loading…</p>
        )}
      </main>
      <footer className={`${SHELL} mt-12 border-t border-line pt-5 pb-10 text-xs text-ink-soft`}>
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
