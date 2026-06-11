import { Tabs } from "@base-ui/react/tabs";
import Section from "./Section.jsx";

// iOS-style segmented control switching between sections of one page.
export default function SegmentedSections({ sections }) {
  if (!sections.length) return null;
  if (sections.length === 1) return <Section section={sections[0]} />;
  return (
    <Tabs.Root defaultValue={sections[0].id}>
      <Tabs.List className="relative z-0 mt-5 flex w-full rounded-full border border-line bg-surface p-1">
        <Tabs.Indicator
          className="absolute top-1 bottom-1 left-0 -z-1 rounded-full bg-accent transition-[transform,width] duration-250 ease-[var(--ease-out-quart)]"
          style={{
            width: "var(--active-tab-width)",
            transform: "translateX(var(--active-tab-left))",
          }}
        />
        {sections.map((s) => (
          <Tabs.Tab
            key={s.id}
            value={s.id}
            className="flex-1 cursor-pointer rounded-full py-1.5 text-center text-[0.8125rem] font-medium text-ink-soft transition-colors duration-150 data-[active]:text-white"
          >
            {s.shortTitle ?? s.title}
          </Tabs.Tab>
        ))}
      </Tabs.List>
      {sections.map((s) => (
        <Tabs.Panel key={s.id} value={s.id}>
          <Section section={s} />
        </Tabs.Panel>
      ))}
    </Tabs.Root>
  );
}
