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

export function numberFormatter(lang, digits = 2) {
  const nf = new Intl.NumberFormat(lang === "sl" ? "sl-SI" : "en-GB", {
    minimumFractionDigits: 0,
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
