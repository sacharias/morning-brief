import { useEffect, useState } from "react";
import { Tabs } from "@base-ui/react/tabs";
import Section from "./components/Section.jsx";
import SegmentedSections from "./components/SegmentedSections.jsx";
import TodayPage from "./components/TodayPage.jsx";
import DayPicker from "./components/DayPicker.jsx";

const DATA_BASE = `${import.meta.env.BASE_URL}data`;
const SHELL = "mx-auto w-full max-w-[680px] px-5";

// Pages of the bottom tab bar. Sections pick a page via their `page` field
// (falling back to this id map); anything unmapped lands on Today.
const PAGES = [
  { id: "today", label: "Today" },
  { id: "x", label: "X" },
  { id: "code", label: "Code" },
  { id: "papers", label: "Papers" },
];

const ID_TO_PAGE = {
  "top-x-posts": "x",
  "x-bookmarks": "x",
  "github-trending": "code",
  "custom-trending": "code",
  "hf-papers": "papers",
};

const TAB_ICONS = {
  today: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" className="size-6">
      <circle cx="12" cy="14" r="4" />
      <path d="M12 6v2M5 14H3m18 0h-2M6.3 8.3 4.9 6.9m12.8 1.4 1.4-1.4M4 19h16" />
    </svg>
  ),
  x: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" className="size-6">
      <path d="M5 4l14 16M19 4 5 20" />
    </svg>
  ),
  code: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-6">
      <path d="m8 7-5 5 5 5m8-10 5 5-5 5" />
    </svg>
  ),
  papers: (
    <svg viewBox="0 0 24 24" fill="none" stroke="currentColor" strokeWidth="1.8" strokeLinecap="round" strokeLinejoin="round" className="size-6">
      <path d="M7 3h7l4 4v14H7zM14 3v4h4M10 12h6m-6 4h6" />
    </svg>
  ),
};

async function fetchJson(url) {
  const res = await fetch(url, { cache: "no-cache" });
  if (!res.ok) throw new Error(`${res.status} ${res.statusText} for ${url}`);
  return res.json();
}

function pageOf(section) {
  return section.page ?? ID_TO_PAGE[section.id] ?? "today";
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
      <div className={`${SHELL} py-12 text-center text-ink-soft`}>
        <p>Could not load the brief.</p>
        <p className="text-[0.8125rem]">{error}</p>
      </div>
    );
  }

  const sections = brief?.sections ?? [];
  const byPage = Object.fromEntries(PAGES.map((p) => [p.id, sections.filter((s) => pageOf(s) === p.id)]));

  return (
    <Tabs.Root defaultValue="today">
      <header className="sticky top-0 z-10 border-b border-line bg-paper/90 backdrop-blur-sm">
        <div className={`${SHELL} flex items-center justify-between gap-4 py-3`}>
          <span className="font-serif text-lg font-semibold">Morning Brief</span>
          {index && index.days.length > 1 && (
            <DayPicker days={index.days} selected={day} onSelect={setDay} />
          )}
        </div>
      </header>

      <main className={`${SHELL} pb-28`}>
        {brief ? (
          <>
            <Tabs.Panel value="today">
              <TodayPage brief={brief} extraSections={byPage.today} />
              <p className="mt-8 text-xs text-ink-soft">
                Generated{" "}
                {brief.generatedAt &&
                  new Date(brief.generatedAt).toLocaleString(undefined, {
                    dateStyle: "medium",
                    timeStyle: "short",
                  })}
              </p>
            </Tabs.Panel>
            <Tabs.Panel value="x">
              {byPage.x.map((s) => (
                <Section key={s.id} section={s} />
              ))}
            </Tabs.Panel>
            <Tabs.Panel value="code">
              <SegmentedSections sections={byPage.code} />
            </Tabs.Panel>
            <Tabs.Panel value="papers">
              {byPage.papers.map((s) => (
                <Section key={s.id} section={s} />
              ))}
            </Tabs.Panel>
          </>
        ) : (
          <p className="py-12 text-center text-ink-soft">Loading…</p>
        )}
      </main>

      <Tabs.List className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-paper/95 backdrop-blur-sm pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto flex w-full max-w-[680px]">
          {PAGES.map((p) => (
            <Tabs.Tab
              key={p.id}
              value={p.id}
              className="flex flex-1 cursor-pointer flex-col items-center gap-0.5 py-2.5 text-[0.65rem] font-medium text-ink-soft transition-colors data-[active]:text-accent"
            >
              {TAB_ICONS[p.id]}
              {p.label}
            </Tabs.Tab>
          ))}
        </div>
      </Tabs.List>
    </Tabs.Root>
  );
}
