export default function DayPicker({ days, selected, onSelect }) {
  return (
    <label className="day-picker">
      <span className="visually-hidden">Choose a day</span>
      <select value={selected ?? ""} onChange={(e) => onSelect(e.target.value)}>
        {days.map((d) => (
          <option key={d} value={d}>
            {d}
          </option>
        ))}
      </select>
    </label>
  );
}
