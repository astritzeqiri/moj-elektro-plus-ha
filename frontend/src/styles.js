// Styles use Home Assistant theme variables, so light/dark themes apply.

export const STYLES = `
:host {
  display: block;
  min-height: 100vh;
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
  font-family: var(--ha-font-family-body, var(--paper-font-body1_-_font-family, Roboto, sans-serif));
  --me-import: var(--energy-grid-consumption-color, #488fc2);
  --me-export: var(--energy-grid-return-color, #8353d1);
  --me-flagged: var(--warning-color, #ffa600);
  --me-missing: var(--disabled-text-color, #bdbdbd);
  --me-ok: var(--success-color, #43a047);
  --me-radius: var(--ha-card-border-radius, 12px);
  --me-line: var(--divider-color, rgba(0, 0, 0, 0.12));
  --me-quiet: var(--secondary-text-color, #727272);
  --me-hover: rgba(var(--rgb-primary-text-color, 33, 33, 33), 0.06);
  --me-press: rgba(var(--rgb-primary-color, 3, 169, 244), 0.14);
}
* { box-sizing: border-box; }
::selection { background: var(--me-press); }
.visually-hidden {
  position: absolute; width: 1px; height: 1px; overflow: hidden;
  clip: rect(0 0 0 0); white-space: nowrap;
}
.ic { width: 20px; height: 20px; fill: currentColor; flex: none; }

/* Header bar, matching Home Assistant's own panels. */
.toolbar {
  display: flex; align-items: center; gap: 4px;
  min-height: var(--header-height, 56px); padding: 0 12px 0 16px;
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, var(--text-primary-color, #fff));
  border-bottom: var(--app-header-border-bottom, none);
  position: sticky; top: 0; z-index: 2;
  padding-top: env(safe-area-inset-top);
}
.toolbar h1 { font-size: 20px; font-weight: 400; margin: 0 0 0 4px; }

.page { max-width: 1120px; margin: 0 auto; padding: 16px 24px 32px; display: grid; gap: 16px; }
/* Grid items default to their content width; let wide rows scroll instead. */
.page > * { min-width: 0; }

/* Buttons */
button {
  font: inherit; font-size: 14px; font-weight: 500; cursor: pointer;
  border-radius: 18px; padding: 0 16px; min-height: 36px;
  border: 1px solid var(--primary-color); background: var(--primary-color);
  color: var(--text-primary-color, #fff);
}
button:disabled { opacity: 0.45; cursor: default; }
.chip {
  background: transparent; color: var(--primary-text-color);
  border-color: var(--me-line); font-weight: 400;
}
.chip:not(:disabled):hover { background: var(--me-hover); }
.chip[aria-pressed="true"] {
  background: var(--me-press); color: var(--primary-color);
  border-color: transparent; font-weight: 500;
}
.icon-btn {
  display: inline-grid; place-items: center; width: 40px; min-height: 40px; padding: 0;
  border: 0; border-radius: 50%; background: transparent; color: inherit;
}
.icon-btn:not(:disabled):hover { background: var(--me-hover); }
.text-btn {
  display: inline-flex; align-items: center; gap: 6px; padding: 0 12px;
  border: 0; background: transparent; color: var(--primary-color);
}
.text-btn:not(:disabled):hover { background: var(--me-press); }
button:focus-visible, select:focus-visible, input:focus-visible,
#chart:focus-visible {
  outline: 2px solid var(--primary-color); outline-offset: 2px;
}

/* Range controls */
.controls { display: flex; flex-wrap: wrap; align-items: center; gap: 8px 12px; }
.presets { display: flex; flex-wrap: wrap; gap: 6px; }
.chip[aria-expanded="true"] { border-color: var(--primary-color); }
.meter-pick select { min-width: 200px; }
select, input {
  font: inherit; font-size: 14px; color: var(--primary-text-color); min-height: 36px;
  background: var(--card-background-color, #fff);
  border: 1px solid var(--me-line); border-radius: 8px; padding: 4px 10px;
}
.custom-fields { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; flex-basis: 100%; }
.custom-fields[hidden] { display: none; }
.field { display: grid; gap: 4px; font-size: 12px; color: var(--me-quiet); }

/* Period heading: what the numbers below describe. */
.period { display: grid; gap: 2px; padding-top: 8px; }
.period-row { display: flex; flex-wrap: wrap; align-items: center; justify-content: space-between; gap: 8px; }
.period-title { display: flex; align-items: center; gap: 4px; min-width: 0; margin-left: -8px; }
.period h2 { font-size: 24px; font-weight: 400; line-height: 1.25; margin: 0 4px; text-wrap: balance; }
.period-actions { display: flex; flex-wrap: wrap; gap: 4px; }
.meter-name { margin: 0; color: var(--me-quiet); font-size: 14px; }

/* Summary: one surface, the total leads, the other figures follow. */
.summary {
  display: grid; grid-template-columns: minmax(220px, auto) 1fr; gap: 24px; align-items: start;
  background: var(--card-background-color, #fff); border: 1px solid var(--me-line);
  border-radius: var(--me-radius); padding: 20px 24px;
}
.total { display: grid; gap: 6px; }
.total-label, .figures dt { font-size: 13px; color: var(--me-quiet); }
.total-value { font-size: 40px; line-height: 1.1; font-weight: 400; font-variant-numeric: tabular-nums; }
.total-value small, .figures small { font-size: 0.5em; color: var(--me-quiet); font-weight: 400; }
.total-meta { display: flex; flex-wrap: wrap; align-items: center; gap: 6px 10px; font-size: 13px; }
.pill { display: inline-block; padding: 2px 10px; border-radius: 10px; font-size: 12px; font-weight: 500; }
.pill.ok { color: var(--me-ok); background: rgba(var(--rgb-success-color, 67, 160, 71), 0.14); }
.pill.partial { color: var(--primary-text-color); background: rgba(var(--rgb-warning-color, 255, 166, 0), 0.22); }
.quiet { color: var(--me-quiet); }
.figures {
  margin: 0; display: grid; grid-template-columns: repeat(auto-fit, minmax(150px, 1fr));
  gap: 16px 24px; padding-left: 24px; border-left: 1px solid var(--me-line); align-self: stretch;
}
.figures div { display: grid; gap: 4px; align-content: start; }
.figures dd { margin: 0; font-size: 20px; font-variant-numeric: tabular-nums; }
.figures dd .quiet { font-size: 14px; }
.sub { display: block; font-size: 12px; color: var(--me-quiet); margin-top: 2px; }

/* Chart */
.card {
  background: var(--card-background-color, #fff);
  border-radius: var(--me-radius); border: 1px solid var(--me-line);
  box-shadow: var(--ha-card-box-shadow, none); padding: 16px 20px;
}
h2 { font-size: 16px; font-weight: 500; margin: 0; }
.chart-head { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.chart-tools, .seg { display: flex; flex-wrap: wrap; gap: 6px; }
.chart-wrap { width: 100%; overflow: hidden; }
#chart { width: 100%; border-radius: 8px; }
svg:not(.ic) { display: block; max-width: 100%; height: auto; }
svg .grid { stroke: var(--me-line); stroke-width: 1; }
svg .zero { stroke: var(--me-quiet); stroke-width: 1; }
svg .axis { fill: var(--me-quiet); font-size: 11px; font-variant-numeric: tabular-nums; }
svg .bar.import { fill: var(--me-import); }
svg .bar.export { fill: var(--me-export); }
svg .bar.flagged { fill: var(--me-flagged); }
svg .bar.partial { opacity: 0.6; }
svg .missing { fill: var(--me-missing); }
svg .active { stroke: var(--primary-text-color); stroke-width: 1.5; }
svg .hit { fill: transparent; }
.tooltip { min-height: 22px; font-size: 13px; margin-top: 6px; font-variant-numeric: tabular-nums; }
.legend { display: flex; flex-wrap: wrap; gap: 6px 16px; font-size: 12px; color: var(--me-quiet); margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.sw.import { background: var(--me-import); } .sw.export { background: var(--me-export); }
.sw.flagged { background: var(--me-flagged); } .sw.missing { background: var(--me-missing); }
.table-wrap { max-height: 420px; overflow: auto; margin-top: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; font-variant-numeric: tabular-nums; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--me-line); }
thead th { position: sticky; top: 0; background: var(--card-background-color, #fff); }

/* Delayed-data notice and data status: always visible, never loud. */
.status {
  display: flex; flex-wrap: wrap; align-items: center; gap: 12px 32px;
  padding: 14px 0 0; border-top: 1px solid var(--me-line); font-size: 14px;
}
.delayed { display: flex; gap: 10px; align-items: flex-start; flex: 1 1 100%; color: var(--me-quiet); }
.delayed p { margin: 0; max-width: 72ch; }
.delayed strong { color: var(--primary-text-color); font-weight: 500; }
.delayed .ic { color: var(--info-color, #039be5); margin-top: 1px; }
.facts { margin: 0; display: flex; flex-wrap: wrap; gap: 8px 32px; }
.facts dt { font-size: 12px; color: var(--me-quiet); }
.facts dd { margin: 0; font-variant-numeric: tabular-nums; }
.progress { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.progress progress { width: 180px; height: 6px; accent-color: var(--primary-color); }
.progress.ok { color: var(--me-ok); }
.progress.warn, .warn { color: var(--error-color, #db4437); }
.actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; margin-left: auto; }
.muted, .foot { color: var(--me-quiet); font-size: 13px; }
.foot { margin: 0; }

/* States */
.banner { padding: 10px 14px; border-radius: 8px; background: var(--card-background-color); border: 1px solid currentColor; }
.banner.info { color: var(--info-color, #039be5); }
.loading { opacity: 0.55; transition: opacity 0.2s ease-out; }
.state { padding: 32px 16px; text-align: center; color: var(--me-quiet); }
.error h2 { color: var(--error-color, #db4437); }

@media (max-width: 720px) {
  .page { padding: 12px 16px 24px; gap: 14px; }
  .summary { grid-template-columns: 1fr; gap: 16px; padding: 16px; }
  .figures { padding-left: 0; border-left: 0; padding-top: 16px; border-top: 1px solid var(--me-line); grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .total-value { font-size: 34px; }
  .period h2 { font-size: 20px; }
  .card { padding: 14px; }
  .meter-pick, .meter-pick select { width: 100%; }
  /* One swipeable row of presets instead of four rows of chips. */
  .controls { display: grid; grid-template-columns: minmax(0, 1fr); }
  .presets {
    flex-wrap: nowrap; overflow-x: auto; scrollbar-width: none; min-width: 0;
    margin: 0 -16px; padding: 2px 16px; scroll-padding-inline: 16px;
  }
  .presets::-webkit-scrollbar { display: none; }
  .presets .chip { flex: none; }
  .custom-fields .field { flex: 1 1 130px; }
  .actions { margin-left: 0; }
}
@media (prefers-reduced-motion: reduce) { .loading { transition: none; } }
`;
