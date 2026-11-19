// Date-range presets. All dates are plain YYYY-MM-DD strings (Ljubljana days).

const pad = (n) => String(n).padStart(2, "0");

export function iso(d) {
  return `${d.getUTCFullYear()}-${pad(d.getUTCMonth() + 1)}-${pad(d.getUTCDate())}`;
}

export function parse(value) {
  const [y, m, d] = value.split("-").map(Number);
  return new Date(Date.UTC(y, m - 1, d));
}

export function addDays(value, days) {
  const d = parse(value);
  d.setUTCDate(d.getUTCDate() + days);
  return iso(d);
}

export function monthStart(value) {
  return `${value.slice(0, 7)}-01`;
}

export function addMonths(value, months) {
  const d = parse(monthStart(value));
  d.setUTCMonth(d.getUTCMonth() + months);
  return iso(d);
}

export function isValidDate(value) {
  if (!/^\d{4}-\d{2}-\d{2}$/.test(value || "")) return false;
  return iso(parse(value)) === value;
}

/** Today's date in Europe/Ljubljana, independent of the browser's zone. */
export function ljubljanaToday(now = new Date()) {
  const parts = new Intl.DateTimeFormat("en-CA", {
    timeZone: "Europe/Ljubljana",
    year: "numeric",
    month: "2-digit",
    day: "2-digit",
  }).formatToParts(now);
  const get = (type) => parts.find((p) => p.type === type).value;
  return `${get("year")}-${get("month")}-${get("day")}`;
}

export const PRESETS = ["latest", "last7", "last30", "thisMonth", "prevMonth", "last12"];

/**
 * Resolve a preset to an inclusive range. Rolling presets end on the latest
 * day with data (readings are delayed), so they never start with empty days.
 */
export function presetRange(preset, latestDay, today) {
  const anchor = latestDay || addDays(today, -1);
  switch (preset) {
    case "latest":
      return { start: anchor, end: anchor };
    case "last7":
      return { start: addDays(anchor, -6), end: anchor };
    case "last30":
      return { start: addDays(anchor, -29), end: anchor };
    case "thisMonth":
      return { start: monthStart(today), end: today };
    case "prevMonth": {
      const start = addMonths(today, -1);
      return { start, end: addDays(monthStart(today), -1) };
    }
    case "last12":
      return { start: addMonths(today, -11), end: today };
    default:
      throw new Error(`unknown preset ${preset}`);
  }
}

export function spanDays(start, end) {
  return Math.round((parse(end) - parse(start)) / 86400000) + 1;
}
