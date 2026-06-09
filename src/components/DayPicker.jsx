export default function DayPicker({ days, selected, onSelect }) {
  return (
    <label className="day-picker">
      <span className="sr-only">Choose a day</span>
      <select
        className="appearance-none rounded-full border border-line bg-surface py-1 pr-7 pl-3 text-[0.8125rem] text-ink"
        value={selected ?? ""}
        onChange={(e) => onSelect(e.target.value)}
      >
        {days.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
    </label>
  );
}
