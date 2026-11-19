// Small dependency-free SVG bar chart. Colours come from HA theme variables.

import { escapeHtml } from "./format.js";

const PAD = { top: 12, right: 8, bottom: 26, left: 48 };

function niceMax(value) {
  if (!(value > 0)) return 1;
  const exp = 10 ** Math.floor(Math.log10(value));
  for (const step of [1, 2, 2.5, 5, 10]) {
    if (step * exp >= value) return step * exp;
  }
  return 10 * exp;
}

/**
 * @param {object} opts
 * @param {Array} opts.points  server points
 * @param {string} opts.resolution  interval | day | month
 * @param {string} opts.mode  energy | power (power only for intervals)
 * @param {number} opts.width
 * @param {number} opts.height
 * @param {number|null} opts.active  highlighted index
 * @param {(p: object) => string} opts.label  x label for a point
 * @param {(v: number) => string} opts.fmt  number formatter
 */
export function renderChart(opts) {
  const { points, resolution, mode, width, height, active, label, fmt } = opts;
  const factor = resolution === "interval" && mode === "power" ? 4 : 1;
  const hasExport = points.some((p) => p.export !== undefined && p.export !== null);
  const imports = points.map((p) => (p.import == null ? null : p.import * factor));
  const exports = points.map((p) => (p.export == null ? null : p.export * factor));
  const maxUp = niceMax(Math.max(0, ...imports.filter((v) => v != null)));
  const maxDown = hasExport ? niceMax(Math.max(0, ...exports.filter((v) => v != null))) : 0;
  const plotW = Math.max(10, width - PAD.left - PAD.right);
  const plotH = Math.max(10, height - PAD.top - PAD.bottom);
  const total = maxUp + maxDown || 1;
  const zeroY = PAD.top + (plotH * maxUp) / total;
  const scale = plotH / total;
  const n = Math.max(points.length, 1);
  const slot = plotW / n;
  const barW = Math.max(1, slot * (n > 200 ? 1 : 0.72));
  const parts = [];

  // Grid and axis labels.
  for (const frac of [0, 0.5, 1]) {
    const v = maxUp * frac;
    const y = zeroY - v * scale;
    parts.push(
      `<line x1="${PAD.left}" x2="${width - PAD.right}" y1="${y}" y2="${y}" class="grid"/>`,
      `<text x="${PAD.left - 6}" y="${y + 4}" class="axis" text-anchor="end">${escapeHtml(fmt(v))}</text>`,
    );
  }
  if (hasExport) {
    const y = zeroY + maxDown * scale;
    parts.push(
      `<line x1="${PAD.left}" x2="${width - PAD.right}" y1="${y}" y2="${y}" class="grid"/>`,
      `<text x="${PAD.left - 6}" y="${y + 4}" class="axis" text-anchor="end">−${escapeHtml(fmt(maxDown))}</text>`,
    );
  }

  points.forEach((p, i) => {
    const x = PAD.left + i * slot + (slot - barW) / 2;
    const cls = [];
    if (i === active) cls.push("active");
    // Only single 15-minute values are coloured by quality; for totals the
    // flagged count is shown in the tooltip and table instead.
    const flagged = resolution === "interval" && p.import_q && p.import_q.length > 0;
    const partial = resolution !== "interval" && p.present > 0 && p.present < p.expected;
    if (imports[i] == null) {
      // Missing data is drawn as a marker, never as a zero-height bar.
      parts.push(
        `<rect x="${x}" y="${zeroY - 3}" width="${barW}" height="3" class="missing ${cls.join(" ")}" data-i="${i}"/>`,
      );
    } else {
      const h = Math.max(imports[i] * scale, imports[i] > 0 ? 1 : 0);
      parts.push(
        `<rect x="${x}" y="${zeroY - h}" width="${barW}" height="${h}" class="bar import ${flagged ? "flagged" : ""} ${partial ? "partial" : ""} ${cls.join(" ")}" data-i="${i}"/>`,
      );
    }
    if (hasExport && exports[i] != null) {
      const h = Math.max(exports[i] * scale, exports[i] > 0 ? 1 : 0);
      parts.push(
        `<rect x="${x}" y="${zeroY}" width="${barW}" height="${h}" class="bar export ${cls.join(" ")}" data-i="${i}"/>`,
      );
    }
    // Hit area for pointer selection.
    parts.push(
      `<rect x="${PAD.left + i * slot}" y="${PAD.top}" width="${slot}" height="${plotH}" class="hit" data-i="${i}"/>`,
    );
  });

  parts.push(
    `<line x1="${PAD.left}" x2="${width - PAD.right}" y1="${zeroY}" y2="${zeroY}" class="zero"/>`,
  );

  // X labels: at most ~8, evenly spaced.
  const every = Math.max(1, Math.ceil(n / Math.max(2, Math.floor(plotW / 70))));
  points.forEach((p, i) => {
    if (i % every) return;
    const x = PAD.left + i * slot + slot / 2;
    parts.push(
      `<text x="${x}" y="${height - 8}" class="axis" text-anchor="middle">${escapeHtml(label(p))}</text>`,
    );
  });

  return `<svg viewBox="0 0 ${width} ${height}" width="${width}" height="${height}" aria-hidden="true" focusable="false">${parts.join("")}</svg>`;
}
