function formatDay(iso) {
  const date = new Date(`${iso}T00:00:00`);
  if (Number.isNaN(date.getTime())) return iso;
  return date.toLocaleDateString("en-US", { weekday: "short", month: "short", day: "numeric" });
}

export default function DayPicker({ days, selected, onSelect }) {
  return (
    <label className="relative inline-flex items-center">
      <span className="sr-only">Choose a day</span>
      <select
        className="cursor-pointer appearance-none rounded-full border border-line bg-surface py-1.5 pr-8 pl-3.5 text-[0.8125rem] font-medium text-ink transition-colors duration-150 active:bg-paper"
        value={selected ?? ""}
        onChange={(e) => onSelect(e.target.value)}
      >
        {days.map((d) => (
          <option key={d} value={d}>
            {formatDay(d)}
          </option>
        ))}
      </select>
      <svg
        className="pointer-events-none absolute right-3 size-3.5 text-ink-soft"
        viewBox="0 0 16 16"
        fill="none"
        stroke="currentColor"
        strokeWidth="1.8"
        strokeLinecap="round"
        strokeLinejoin="round"
        aria-hidden="true"
      >
        <path d="m4.5 6.25 3.5 3.5 3.5-3.5" />
      </svg>
    </label>
  );
}
