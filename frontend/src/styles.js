// Styles use Home Assistant theme variables, so light/dark themes apply.

export const STYLES = `
:host {
  display: block;
  min-height: 100vh;
  background: var(--primary-background-color, #fafafa);
  color: var(--primary-text-color, #212121);
  font-family: var(--paper-font-body1_-_font-family, var(--ha-font-family-body, Roboto, sans-serif));
  --me-import: var(--energy-grid-consumption-color, #488fc2);
  --me-export: var(--energy-grid-return-color, #8353d1);
  --me-flagged: var(--warning-color, #ffa600);
  --me-missing: var(--disabled-text-color, #bdbdbd);
  --me-radius: var(--ha-card-border-radius, 12px);
}
* { box-sizing: border-box; }
.toolbar {
  display: flex; align-items: center; gap: 8px;
  height: var(--header-height, 56px); padding: 0 16px;
  background: var(--app-header-background-color, var(--primary-color));
  color: var(--app-header-text-color, var(--text-primary-color, #fff));
  position: sticky; top: 0; z-index: 2;
  padding-top: env(safe-area-inset-top);
}
.toolbar h1 { font-size: 20px; font-weight: 400; margin: 0; }
.page { max-width: 1200px; margin: 0 auto; padding: 16px; display: grid; gap: 16px; }
.card {
  background: var(--card-background-color, #fff);
  border-radius: var(--me-radius);
  box-shadow: var(--ha-card-box-shadow, none);
  border: 1px solid var(--divider-color, rgba(0,0,0,.12));
  padding: 16px;
}
h2 { font-size: 16px; font-weight: 500; margin: 0; }
button {
  font: inherit; cursor: pointer; border-radius: 8px; padding: 8px 14px; min-height: 40px;
  border: 1px solid var(--primary-color); background: var(--primary-color);
  color: var(--text-primary-color, #fff);
}
button.secondary, button.chip {
  background: transparent; color: var(--primary-text-color);
  border-color: var(--divider-color, rgba(0,0,0,.2));
}
button.chip[aria-pressed="true"] {
  background: var(--primary-color); color: var(--text-primary-color, #fff); border-color: var(--primary-color);
}
button.icon { background: transparent; border: 0; color: inherit; font-size: 22px; min-width: 40px; }
button:disabled { opacity: .5; cursor: default; }
button:focus-visible, select:focus-visible, input:focus-visible, #chart:focus-visible {
  outline: 2px solid var(--primary-color); outline-offset: 2px;
}
.controls { display: grid; gap: 12px; }
.presets { display: flex; flex-wrap: wrap; gap: 8px; }
.custom { display: flex; flex-wrap: wrap; gap: 8px; align-items: end; }
.field { display: grid; gap: 4px; font-size: 12px; color: var(--secondary-text-color); }
select, input {
  font: inherit; font-size: 14px; color: var(--primary-text-color); min-height: 40px;
  background: var(--input-fill-color, var(--secondary-background-color, transparent));
  border: 1px solid var(--divider-color, rgba(0,0,0,.2)); border-radius: 8px; padding: 6px 10px;
}
.status { display: grid; gap: 12px; }
.delayed { padding: 10px 12px; border-radius: 8px; background: rgba(var(--rgb-info-color, 3,155,229), .12); }
dl { margin: 0; display: flex; flex-wrap: wrap; gap: 8px 32px; }
dt { font-size: 12px; color: var(--secondary-text-color); }
dd { margin: 0; font-weight: 500; }
.actions { display: flex; flex-wrap: wrap; gap: 8px; align-items: center; }
.progress { display: flex; flex-wrap: wrap; align-items: center; gap: 8px; }
.progress progress { flex: 1 1 160px; height: 8px; accent-color: var(--primary-color); }
.progress.ok { color: var(--success-color, #43a047); }
.progress.warn, .warn { color: var(--error-color, #db4437); }
.muted, .foot { color: var(--secondary-text-color); font-size: 13px; }
.banner { padding: 10px 14px; border-radius: 8px; background: var(--card-background-color); border: 1px solid currentColor; }
.banner.info { color: var(--info-color, #039be5); }
.stats { display: grid; grid-template-columns: repeat(auto-fit, minmax(170px, 1fr)); gap: 12px; }
.stat {
  background: var(--card-background-color, #fff); border-radius: var(--me-radius);
  border: 1px solid var(--divider-color, rgba(0,0,0,.12)); padding: 14px; display: grid; gap: 4px; align-content: start;
}
.stat .label { font-size: 13px; color: var(--secondary-text-color); }
.stat .value { font-size: 24px; font-weight: 500; }
.stat .value.small { font-size: 15px; font-weight: 400; }
.stat small { font-size: 13px; color: var(--secondary-text-color); }
.stat .sub { font-size: 12px; color: var(--secondary-text-color); display: block; }
.badge { display: inline-block; padding: 1px 8px; border-radius: 10px; background: var(--me-flagged); color: #000; }
.loading { opacity: .55; transition: opacity .2s; }
.chart-head { display: flex; flex-wrap: wrap; gap: 8px; justify-content: space-between; align-items: center; margin-bottom: 8px; }
.chart-tools, .seg { display: flex; flex-wrap: wrap; gap: 6px; }
.chart-wrap { width: 100%; overflow: hidden; }
#chart { width: 100%; border-radius: 8px; }
svg { display: block; max-width: 100%; height: auto; }
svg .grid { stroke: var(--divider-color, rgba(0,0,0,.12)); stroke-width: 1; }
svg .zero { stroke: var(--secondary-text-color); stroke-width: 1; }
svg .axis { fill: var(--secondary-text-color); font-size: 11px; }
svg .bar.import { fill: var(--me-import); }
svg .bar.export { fill: var(--me-export); }
svg .bar.flagged { fill: var(--me-flagged); }
svg .bar.partial { opacity: .6; }
svg .missing { fill: var(--me-missing); }
svg .active { stroke: var(--primary-text-color); stroke-width: 1.5; }
svg .hit { fill: transparent; }
.tooltip { min-height: 22px; font-size: 13px; margin-top: 6px; }
.legend { display: flex; flex-wrap: wrap; gap: 14px; font-size: 12px; color: var(--secondary-text-color); margin-top: 8px; }
.sw { display: inline-block; width: 10px; height: 10px; border-radius: 2px; margin-right: 6px; vertical-align: middle; }
.sw.import { background: var(--me-import); } .sw.export { background: var(--me-export); }
.sw.flagged { background: var(--me-flagged); } .sw.missing { background: var(--me-missing); }
.state { padding: 32px 16px; text-align: center; color: var(--secondary-text-color); }
.error h2 { color: var(--error-color, #db4437); }
.table-wrap { max-height: 420px; overflow: auto; margin-top: 12px; }
table { border-collapse: collapse; width: 100%; font-size: 13px; }
th, td { text-align: left; padding: 6px 8px; border-bottom: 1px solid var(--divider-color, rgba(0,0,0,.12)); }
thead th { position: sticky; top: 0; background: var(--card-background-color, #fff); }
@media (max-width: 600px) {
  .page { padding: 12px; gap: 12px; }
  .stats { grid-template-columns: repeat(2, minmax(0, 1fr)); }
  .stat .value { font-size: 20px; }
  .custom .field { flex: 1 1 130px; }
}
@media (prefers-reduced-motion: reduce) { .loading { transition: none; } }
`;
