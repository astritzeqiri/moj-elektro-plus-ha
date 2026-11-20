// Formatting helpers. Times are always shown in Europe/Ljubljana.

export const TZ = "Europe/Ljubljana";

export function escapeHtml(value) {
  return String(value ?? "")
    .replaceAll("&", "&amp;")
    .replaceAll("<", "&lt;")
    .replaceAll(">", "&gt;")
    .replaceAll('"', "&quot;")
    .replaceAll("'", "&#39;");
}

export function numberFormatter(lang, digits = 2, minDigits = 0) {
  const nf = new Intl.NumberFormat(lang === "sl" ? "sl-SI" : "en-GB", {
    minimumFractionDigits: minDigits,
    maximumFractionDigits: digits,
  });
  return (v) => (v == null || Number.isNaN(v) ? "—" : nf.format(v));
}

function locale(lang) {
  return lang === "sl" ? "sl-SI" : "en-GB";
}

export function formatDateTime(lang, isoString) {
  if (!isoString) return "";
  return new Intl.DateTimeFormat(locale(lang), {
    timeZone: TZ,
    year: "numeric",
    month: "short",
    day: "numeric",
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoString));
}

export function formatTime(lang, isoString) {
  return new Intl.DateTimeFormat(locale(lang), {
    timeZone: TZ,
    hour: "2-digit",
    minute: "2-digit",
  }).format(new Date(isoString));
}

/** A plain YYYY-MM-DD day, formatted without any timezone shift. */
export function formatDay(lang, day, opts = { day: "numeric", month: "short" }) {
  const [y, m, d] = day.split("-").map(Number);
  return new Intl.DateTimeFormat(locale(lang), { timeZone: "UTC", ...opts }).format(
    new Date(Date.UTC(y, m - 1, d)),
  );
}

export function formatMonth(lang, day) {
  return formatDay(lang, day, { month: "short", year: "numeric" });
}

/** "3 – 9 Nov 2026" style range for plain YYYY-MM-DD days. */
export function formatRange(lang, start, end) {
  const toDate = (day) => {
    const [y, m, d] = day.split("-").map(Number);
    return new Date(Date.UTC(y, m - 1, d));
  };
  const fmt = new Intl.DateTimeFormat(locale(lang), {
    timeZone: "UTC",
    day: "numeric",
    month: "short",
    year: "numeric",
  });
  if (typeof fmt.formatRange === "function") return fmt.formatRange(toDate(start), toDate(end));
  return `${fmt.format(toDate(start))} – ${fmt.format(toDate(end))}`;
}
