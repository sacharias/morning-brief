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
  { id: "today", label: "Today", empty: "front-page items" },
  { id: "x", label: "X", empty: "X posts or bookmarks" },
  { id: "code", label: "Code", empty: "trending repositories" },
  { id: "papers", label: "Papers", empty: "papers" },
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

// Loading placeholder shaped like the brief itself: masthead, summary, a group.
function Skeleton() {
  return (
    <div className="pt-6 md:pt-10" role="status" aria-label="Loading the brief">
      <div className="animate-pulse" aria-hidden="true">
        <div className="h-3 w-36 rounded-full bg-line/70" />
        <div className="mt-5 space-y-2.5">
          <div className="h-7 w-full rounded-md bg-line/70" />
          <div className="h-7 w-4/5 rounded-md bg-line/70" />
        </div>
        <div className="mt-7 space-y-3.5">
          {[92, 84, 88, 76].map((w, i) => (
            <div key={i} className="h-3.5 rounded-full bg-line/60" style={{ width: `${w}%` }} />
          ))}
        </div>
        <div className="mt-10 divide-y divide-line overflow-hidden rounded-2xl border border-line bg-surface">
          {[0, 1, 2, 3].map((i) => (
            <div key={i} className="space-y-2.5 px-4 py-4">
              <div className="h-3.5 w-3/5 rounded-full bg-line/60" />
              <div className="h-3 w-11/12 rounded-full bg-line/50" />
            </div>
          ))}
        </div>
      </div>
    </div>
  );
}

function EmptyPage({ label }) {
  return (
    <div className="mt-10 rounded-2xl border border-line bg-surface px-6 py-12 text-center">
      <p className="font-serif text-lg font-semibold">Nothing here today</p>
      <p className="mt-1 text-sm text-ink-soft">No {label} made today’s brief. Check back tomorrow.</p>
    </div>
  );
}

export default function App() {
  const [index, setIndex] = useState(null);
  const [day, setDay] = useState(null);
  const [brief, setBrief] = useState(null);
  const [error, setError] = useState(null);
  const [scrolled, setScrolled] = useState(false);

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

  // The header sits flush with the paper at rest; once content scrolls
  // beneath it, the hairline and blur fade in — the iOS large-title cue.
  useEffect(() => {
    const onScroll = () => setScrolled(window.scrollY > 8);
    onScroll();
    window.addEventListener("scroll", onScroll, { passive: true });
    return () => window.removeEventListener("scroll", onScroll);
  }, []);

  if (error) {
    return (
      <div className={`${SHELL} flex min-h-dvh flex-col items-center justify-center py-12 text-center`}>
        <p className="font-serif text-xl font-semibold">The brief didn’t load</p>
        <p className="mt-2 max-w-[40ch] text-sm text-ink-soft">{error}</p>
        <button
          type="button"
          className="mt-6 cursor-pointer rounded-full border border-line bg-surface px-5 py-2 text-[0.8125rem] font-medium text-ink transition-colors duration-150 hover:border-accent/40 hover:text-accent active:scale-[0.985]"
          onClick={() => window.location.reload()}
        >
          Try again
        </button>
      </div>
    );
  }

  const sections = brief?.sections ?? [];
  const byPage = Object.fromEntries(PAGES.map((p) => [p.id, sections.filter((s) => pageOf(s) === p.id)]));

  return (
    <Tabs.Root defaultValue="today" onValueChange={() => window.scrollTo(0, 0)}>
      <header
        className={`sticky top-0 z-10 border-b transition-colors duration-300 ${
          scrolled ? "border-line bg-paper/90 backdrop-blur-sm" : "border-transparent bg-paper"
        }`}
      >
        <div className={`${SHELL} flex items-center justify-between gap-4 py-3`}>
          <span className="font-serif text-[1.0625rem] font-semibold tracking-[-0.01em]">Morning Brief</span>
          {index && index.days.length > 1 && (
            <DayPicker
              days={index.days}
              selected={day}
              onSelect={(d) => {
                setDay(d);
                window.scrollTo(0, 0);
              }}
            />
          )}
        </div>
      </header>

      <main className={`${SHELL} pb-32`}>
        {brief ? (
          <>
            <Tabs.Panel value="today">
              <TodayPage brief={brief} extraSections={byPage.today} />
            </Tabs.Panel>
            <Tabs.Panel value="x">
              {byPage.x.length ? <SegmentedSections sections={byPage.x} /> : <EmptyPage label={PAGES[1].empty} />}
            </Tabs.Panel>
            <Tabs.Panel value="code">
              {byPage.code.length ? <SegmentedSections sections={byPage.code} /> : <EmptyPage label={PAGES[2].empty} />}
            </Tabs.Panel>
            <Tabs.Panel value="papers">
              {byPage.papers.length ? (
                byPage.papers.map((s) => <Section key={s.id} section={s} />)
              ) : (
                <EmptyPage label={PAGES[3].empty} />
              )}
            </Tabs.Panel>
          </>
        ) : (
          <Skeleton />
        )}
      </main>

      <Tabs.List className="fixed inset-x-0 bottom-0 z-10 border-t border-line bg-paper/95 backdrop-blur-sm pb-[env(safe-area-inset-bottom)]">
        <div className="mx-auto flex w-full max-w-[680px]">
          {PAGES.map((p) => (
            <Tabs.Tab
              key={p.id}
              value={p.id}
              className="flex flex-1 cursor-pointer flex-col items-center gap-0.5 py-2.5 text-[0.65rem] font-medium text-ink-soft transition-[color,transform] duration-200 ease-[var(--ease-out-expo)] active:scale-90 data-[active]:text-accent"
            >
              <span className="mb-tab-icon">{TAB_ICONS[p.id]}</span>
              {p.label}
            </Tabs.Tab>
          ))}
        </div>
      </Tabs.List>
    </Tabs.Root>
  );
}
