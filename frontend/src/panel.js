// "Moj Elektro" sidebar page. Talks only to Home Assistant's authenticated
// WebSocket API (mojelektro_plus/* commands); never to Moj Elektro directly
// and never sees the Moj Elektro API token.

import { renderChart } from "./chart.js";
import {
  PRESETS,
  isValidDate,
  ljubljanaToday,
  presetRange,
  spanDays,
} from "./dates.js";
import {
  escapeHtml as e,
  formatDateTime,
  formatDay,
  formatMonth,
  formatTime,
  numberFormatter,
} from "./format.js";
import { language, translator } from "./i18n.js";
import { STYLES } from "./styles.js";

const DOMAIN = "mojelektro_plus";
const STORAGE_KEY = "mojelektro_plus.selected_meter";
const RETRY_MS = 3000;
const MAX_START_RETRIES = 40;
const STARTING_CODES = new Set(["unknown_command", "not_found"]);

function readStoredMeter() {
  try {
    return window.localStorage.getItem(STORAGE_KEY);
  } catch {
    return null;
  }
}

function storeMeter(id) {
  try {
    window.localStorage.setItem(STORAGE_KEY, id);
  } catch {
    /* private mode: selection is simply not remembered */
  }
}

export class MojElektroPanel extends HTMLElement {
  constructor() {
    super();
    this.attachShadow({ mode: "open" });
    this._state = {
      status: "loading", // loading | ready | error | empty
      meters: [],
      entryId: null,
      preset: "latest",
      start: null,
      end: null,
      data: null,
      dataLoading: false,
      error: null,
      mode: "energy",
      showTable: false,
      active: null,
      notice: null,
    };
    this._seq = 0;
    this._startRetries = 0;
    this._width = 640;
    this._onClick = this._onClick.bind(this);
    this._onChange = this._onChange.bind(this);
    this._onKey = this._onKey.bind(this);
    this._onPointer = this._onPointer.bind(this);
    this.shadowRoot.addEventListener("click", this._onClick);
    this.shadowRoot.addEventListener("change", this._onChange);
    this.shadowRoot.addEventListener("keydown", this._onKey);
    this.shadowRoot.addEventListener("pointermove", this._onPointer);
  }

  // ------------------------------------------------------------ HA properties

  set hass(hass) {
    const first = !this._hass;
    const wasConnected = this._hass?.connected !== false;
    const oldLang = this._lang;
    this._hass = hass;
    this._lang = language(hass);
    this._t = translator(this._lang);
    if (first) {
      this._init();
      return;
    }
    if (oldLang !== this._lang || wasConnected !== (hass.connected !== false)) {
      this._render();
      if (!wasConnected && hass.connected !== false) this._reload();
    }
    if (this._menu) this._menu.hass = hass;
  }

  get hass() {
    return this._hass;
  }

  set narrow(value) {
    const changed = this._narrow !== value;
    this._narrow = value;
    if (changed && this._hass) this._render();
  }

  set panel(value) {
    this._panel = value;
  }

  set route(value) {
    this._route = value;
  }

  connectedCallback() {
    if (!this._resize && typeof ResizeObserver !== "undefined") {
      this._resize = new ResizeObserver((entries) => {
        const width = Math.floor(entries[0].contentRect.width);
        if (width && Math.abs(width - this._width) > 4) {
          this._width = width;
          this._renderChartOnly();
        }
      });
    }
    if (this._hass && !this._unsub && this._initialised) this._subscribe();
  }

  disconnectedCallback() {
    this._resize?.disconnect();
    this._unsubscribe();
    clearTimeout(this._debounce);
    clearTimeout(this._subRetry);
    clearTimeout(this._loadRetry);
  }

  // ------------------------------------------------------------------- data

  _ws(type, payload = {}) {
    return this._hass.callWS({ type: `${DOMAIN}/${type}`, ...payload });
  }

  async _init() {
    this._initialised = true;
    this._render();
    this._subscribe();
    await this._loadMeters(true);
  }

  async _subscribe() {
    if (this._unsub || !this._hass?.connection) return;
    try {
      this._unsub = await this._hass.connection.subscribeMessage(
        (event) => this._onServerUpdate(event),
        { type: `${DOMAIN}/subscribe` },
      );
    } catch {
      // Home Assistant may still be starting; the integration registers its
      // commands during setup. Try again shortly.
      this._unsub = null;
      clearTimeout(this._subRetry);
      if (this.isConnected) this._subRetry = setTimeout(() => this._subscribe(), RETRY_MS);
    }
  }

  _unsubscribe() {
    if (this._unsub) {
      const unsub = this._unsub;
      this._unsub = null;
      Promise.resolve(unsub()).catch(() => {});
    }
  }

  _onServerUpdate(event) {
    if (!event || event.entry_id !== this._state.entryId) {
      this._loadMeters(false);
      return;
    }
    clearTimeout(this._debounce);
    this._debounce = setTimeout(() => this._reload(), 800);
  }

  async _reload() {
    await this._loadMeters(false);
    if (this._state.start) await this._loadData();
  }

  async _loadMeters(initial) {
    try {
      const result = await this._ws("meters");
      this._startRetries = 0;
      const meters = result.meters || [];
      const s = this._state;
      s.meters = meters;
      if (!meters.length) {
        s.status = "empty";
        this._render();
        return;
      }
      if (!meters.some((m) => m.entry_id === s.entryId)) {
        const stored = readStoredMeter();
        s.entryId = meters.some((m) => m.entry_id === stored) ? stored : meters[0].entry_id;
      }
      s.status = "ready";
      if (initial) {
        this._applyPreset("latest");
        return;
      }
      this._render();
    } catch (err) {
      if (STARTING_CODES.has(err?.code) && this._startRetries < MAX_START_RETRIES) {
        // Integration not loaded yet (HA restarting): keep "loading" and retry.
        this._startRetries += 1;
        clearTimeout(this._loadRetry);
        this._loadRetry = setTimeout(() => this._loadMeters(initial), RETRY_MS);
        return;
      }
      this._state.status = "error";
      this._state.error = err?.message || String(err);
      this._render();
    }
  }

  get _meter() {
    return this._state.meters.find((m) => m.entry_id === this._state.entryId) || null;
  }

  _applyPreset(preset) {
    const s = this._state;
    const range = presetRange(preset, this._meter?.latest_day, ljubljanaToday());
    s.preset = preset;
    s.start = range.start;
    s.end = range.end;
    s.active = null;
    this._loadData();
  }

  async _loadData() {
    const s = this._state;
    if (!s.entryId || !s.start) return;
    const seq = ++this._seq;
    s.dataLoading = true;
    s.error = null;
    this._render();
    try {
      const data = await this._ws("data", {
        entry_id: s.entryId,
        start: s.start,
        end: s.end,
        resolution: "auto",
      });
      if (seq !== this._seq) return; // a newer request superseded this one
      s.data = data;
      s.dataLoading = false;
      if (s.active != null && s.active >= data.points.length) s.active = null;
    } catch (err) {
      if (seq !== this._seq) return;
      s.dataLoading = false;
      s.error = err?.message || String(err);
    }
    this._render();
  }

  // ----------------------------------------------------------------- events

  _onClick(ev) {
    const target = ev.target.closest("[data-action]");
    if (!target) {
      const bar = ev.target.closest("[data-i]");
      if (bar) {
        this._state.active = Number(bar.dataset.i);
        this._renderChartOnly();
      }
      return;
    }
    const action = target.dataset.action;
    const s = this._state;
    if (action === "preset") this._applyPreset(target.dataset.preset);
    else if (action === "apply-range") this._applyCustom();
    else if (action === "retry") s.status === "error" ? this._init() : this._loadData();
    else if (action === "refresh") this._refresh(false);
    else if (action === "refresh-range") this._refresh(true);
    else if (action === "backfill") this._backfill();
    else if (action === "csv") this._csv();
    else if (action === "mode") {
      s.mode = target.dataset.mode;
      this._render();
    } else if (action === "table") {
      s.showTable = !s.showTable;
      this._render();
    } else if (action === "menu") {
      this.dispatchEvent(new Event("hass-toggle-menu", { bubbles: true, composed: true }));
    }
  }

  _onChange(ev) {
    if (ev.target.id === "meter") {
      this._state.entryId = ev.target.value;
      storeMeter(ev.target.value);
      this._state.data = null;
      this._applyPreset(this._state.preset === "custom" ? "latest" : this._state.preset);
    }
  }

  _onKey(ev) {
    if (ev.target.id === "chart") {
      const s = this._state;
      const n = s.data?.points?.length || 0;
      if (!n) return;
      let i = s.active ?? -1;
      if (ev.key === "ArrowRight") i = Math.min(n - 1, i + 1);
      else if (ev.key === "ArrowLeft") i = Math.max(0, i < 0 ? n - 1 : i - 1);
      else if (ev.key === "Home") i = 0;
      else if (ev.key === "End") i = n - 1;
      else return;
      ev.preventDefault();
      s.active = i;
      this._renderChartOnly();
    } else if ((ev.target.id === "start" || ev.target.id === "end") && ev.key === "Enter") {
      this._applyCustom();
    }
  }

  _onPointer(ev) {
    const hit = ev.target.closest?.("rect.hit");
    if (!hit) return;
    const i = Number(hit.dataset.i);
    if (i !== this._state.active) {
      this._state.active = i;
      this._renderChartOnly();
    }
  }

  _applyCustom() {
    const root = this.shadowRoot;
    const start = root.getElementById("start")?.value;
    const end = root.getElementById("end")?.value;
    const s = this._state;
    if (!isValidDate(start) || !isValidDate(end) || end < start) {
      s.notice = { kind: "error", text: this._t("errorTitle") };
      this._render();
      return;
    }
    s.preset = "custom";
    s.start = start;
    s.end = end;
    s.notice = null;
    s.active = null;
    this._loadData();
  }

  async _refresh(range) {
    const s = this._state;
    try {
      const payload = { entry_id: s.entryId };
      if (range) Object.assign(payload, { start: s.start, end: s.end });
      await this._ws("refresh", payload);
      s.notice = { kind: "info", text: this._t("started") };
    } catch (err) {
      s.notice = { kind: "error", text: err?.message || String(err) };
    }
    this._render();
    this._reload();
  }

  async _backfill() {
    try {
      await this._ws("backfill", { entry_id: this._state.entryId });
    } catch (err) {
      this._state.notice = { kind: "error", text: err?.message || String(err) };
    }
    this._reload();
  }

  async _csv() {
    const s = this._state;
    try {
      const resolution = s.data?.resolution || "auto";
      const result = await this._ws("csv", {
        entry_id: s.entryId,
        start: s.start,
        end: s.end,
        resolution,
      });
      const blob = new Blob([result.csv], { type: "text/csv;charset=utf-8" });
      const url = URL.createObjectURL(blob);
      const a = document.createElement("a");
      a.href = url;
      a.download = result.filename;
      this.shadowRoot.appendChild(a);
      a.click();
      a.remove();
      setTimeout(() => URL.revokeObjectURL(url), 1000);
    } catch (err) {
      s.notice = { kind: "error", text: err?.message || String(err) };
      this._render();
    }
  }

  // -------------------------------------------------------------- rendering

  _fmt(digits = 2) {
    return numberFormatter(this._lang, digits);
  }

  _pointLabel(p, short = true) {
    const res = this._state.data?.resolution;
    if (res === "interval") return formatTime(this._lang, p.end);
    if (res === "month") return formatMonth(this._lang, p.start);
    return short ? formatDay(this._lang, p.start) : formatDay(this._lang, p.start, { dateStyle: "medium" });
  }

  _render() {
    const t = this._t;
    const s = this._state;
    const offline = this._hass?.connected === false;
    const body = (() => {
      if (s.status === "loading") return `<div class="state" role="status">${e(t("loading"))}</div>`;
      if (s.status === "empty") return `<div class="state">${e(t("noMeters"))}</div>`;
      if (s.status === "error")
        return `<div class="card error" role="alert"><h2>${e(t("errorTitle"))}</h2><p>${e(s.error)}</p><button data-action="retry">${e(t("retry"))}</button></div>`;
      return this._content();
    })();
    this.shadowRoot.innerHTML = `
      <style>${STYLES}</style>
      <div class="toolbar">
        ${this._narrow ? `<span id="menu-slot"></span>` : ""}
        <h1>${e(t("title"))}</h1>
      </div>
      <main class="page" aria-busy="${s.dataLoading || s.status === "loading"}">
        ${offline ? `<div class="banner warn" role="status">${e(t("offline"))}</div>` : ""}
        ${body}
      </main>`;
    this._mountMenu();
    const chart = this.shadowRoot.getElementById("chart-wrap");
    if (chart && this._resize) {
      this._resize.disconnect();
      this._resize.observe(chart);
    }
  }

  _mountMenu() {
    const slot = this.shadowRoot.getElementById("menu-slot");
    if (!slot) return;
    if (customElements.get("ha-menu-button")) {
      const menu = document.createElement("ha-menu-button");
      menu.hass = this._hass;
      menu.narrow = this._narrow;
      slot.appendChild(menu);
      this._menu = menu;
    } else {
      slot.innerHTML = `<button class="icon" data-action="menu" aria-label="${e(this._t("menu"))}">☰</button>`;
    }
  }

  _content() {
    const t = this._t;
    const s = this._state;
    const meter = this._meter;
    const admin = !!this._hass?.user?.is_admin;
    return `
      <section class="controls card" aria-label="${e(t("range"))}">
        <label class="field">${e(t("meter"))}
          <select id="meter">${s.meters
            .map(
              (m) =>
                `<option value="${e(m.entry_id)}" ${m.entry_id === s.entryId ? "selected" : ""}>${e(m.title)}</option>`,
            )
            .join("")}</select>
        </label>
        <div class="presets" role="group" aria-label="${e(t("range"))}">
          ${PRESETS.map(
            (p) =>
              `<button class="chip" data-action="preset" data-preset="${p}" aria-pressed="${s.preset === p}">${e(t(`presets.${p}`))}</button>`,
          ).join("")}
        </div>
        <div class="custom">
          <label class="field">${e(t("from"))}<input id="start" type="date" value="${e(s.start)}" min="${e(meter?.earliest_allowed || "")}"></label>
          <label class="field">${e(t("to"))}<input id="end" type="date" value="${e(s.end)}"></label>
          <button data-action="apply-range">${e(t("apply"))}</button>
        </div>
      </section>
      ${this._statusCard(meter, admin)}
      ${s.notice ? `<div class="banner ${s.notice.kind === "error" ? "warn" : "info"}" role="status">${e(s.notice.text)}</div>` : ""}
      ${this._dataSection(meter, admin)}
      <p class="foot">${e(t("timezoneNote"))} ${e(t("costNote"))}</p>`;
  }

  _statusCard(meter, admin) {
    const t = this._t;
    if (!meter) return "";
    const b = meter.backfill || {};
    const job = meter.job;
    let progress = "";
    if (job) {
      const label = job.kind === "range" ? "rangeRunning" : "backfillRunning";
      progress = `<div class="progress"><span>${e(t(label, { done: job.done + 1 > job.total ? job.total : job.done + 1, total: job.total }))}</span>
        <progress max="${job.total}" value="${job.done}" aria-label="${e(t("backfill"))}"></progress></div>`;
    } else if (b.state === "error") {
      progress = `<div class="progress warn">${e(t("backfillError", { error: b.error || "" }))}
        ${admin ? `<button data-action="backfill">${e(t("backfillRetry"))}</button>` : ""}</div>`;
    } else if (b.state === "complete") {
      progress = `<div class="progress ok">${e(t("backfillComplete"))}</div>`;
    }
    return `
      <section class="card status" aria-label="${e(t("delayedTitle"))}">
        <div class="delayed"><strong>${e(t("delayedTitle"))}</strong> — ${e(t("delayedText"))}</div>
        <dl>
          <div><dt>${e(t("latestMeasurement"))}</dt><dd>${meter.latest_reading ? e(formatDateTime(this._lang, meter.latest_reading)) : "—"}</dd></div>
          <div><dt>${e(t("lastRefresh"))}</dt><dd>${meter.last_success ? e(formatDateTime(this._lang, meter.last_success)) : e(t("never"))}</dd></div>
        </dl>
        ${progress}
        <div class="actions">
          ${
            admin
              ? `<button data-action="refresh">${e(t("refresh"))}</button>
                 <button data-action="refresh-range" class="secondary">${e(t("refreshRange"))}</button>`
              : `<span class="muted">${e(t("adminOnly"))}</span>`
          }
          <button data-action="csv" class="secondary" ${this._state.data ? "" : "disabled"}>${e(t("exportCsv"))}</button>
        </div>
      </section>`;
  }

  _dataSection(meter, _admin) {
    const t = this._t;
    const s = this._state;
    if (s.error && !s.data) {
      return `<div class="card error" role="alert"><h2>${e(t("errorTitle"))}</h2><p>${e(s.error)}</p><button data-action="retry">${e(t("retry"))}</button></div>`;
    }
    if (!s.data) return `<div class="state" role="status">${e(t("loading"))}</div>`;
    const d = s.data;
    const sum = d.summary;
    const hasAny = d.points.some((p) => p.import != null);
    const fmt = this._fmt(2);
    const imp = sum.import;
    const exportCard = (() => {
      if (d.export_status !== "available")
        return `<div class="stat"><span class="label">${e(t("exported"))}</span><span class="value small">${e(t(d.export_status === "not_provided" ? "exportNotProvided" : "exportUnknown"))}</span></div>`;
      return `<div class="stat"><span class="label">${e(t("exported"))}</span><span class="value">${fmt(sum.export?.total)} <small>${t("kwh")}</small></span></div>`;
    })();
    const peak = sum.peak
      ? `${this._fmt(3)(sum.peak.power_kw)} <small>${t("kw")}</small><span class="sub">${e(formatDateTime(this._lang, sum.peak.interval_end))}</span>`
      : "—";
    const error = s.error
      ? `<div class="banner warn" role="alert">${e(s.error)} <button data-action="retry">${e(t("retry"))}</button></div>`
      : "";
    const chartTitle = t(
      d.resolution === "interval" ? "chartIntervals" : d.resolution === "day" ? "chartDays" : "chartMonths",
    );
    const empty = !hasAny
      ? `<div class="state">${e(meter?.backfill?.state === "running" || meter?.job ? t("noDataBackfill") : t("noData"))}</div>`
      : "";
    return `
      ${error}
      <section class="stats ${s.dataLoading ? "loading" : ""}" aria-live="polite">
        <div class="stat"><span class="label">${e(t("imported"))}</span><span class="value">${fmt(imp.total)} <small>${t("kwh")}</small></span>
          <span class="sub">${imp.complete ? e(t("complete")) : `<span class="badge">${e(t("partial"))}</span>`}</span></div>
        ${exportCard}
        <div class="stat"><span class="label">${e(t("dailyAverage"))}</span><span class="value">${fmt(sum.daily_average)} <small>${t("kwh")}</small></span><span class="sub">${e(t("dailyAverageHint"))}</span></div>
        <div class="stat"><span class="label">${e(t("peak"))}</span><span class="value">${peak}</span></div>
        <div class="stat"><span class="label">${e(t("coverage"))}</span><span class="value">${this._fmt(1)(imp.coverage)} <small>%</small></span>
          <span class="sub">${imp.flagged ? e(t("flagged", { n: imp.flagged })) : e(t("noFlagged"))}</span></div>
      </section>
      <section class="card chart-card ${s.dataLoading ? "loading" : ""}">
        <div class="chart-head">
          <h2>${e(chartTitle)}</h2>
          <div class="chart-tools">
            ${
              d.resolution === "interval"
                ? `<div role="group" class="seg">
                    <button class="chip" data-action="mode" data-mode="energy" aria-pressed="${s.mode === "energy"}">${e(t("energy"))}</button>
                    <button class="chip" data-action="mode" data-mode="power" aria-pressed="${s.mode === "power"}">${e(t("power"))}</button>
                  </div>`
                : ""
            }
            <button class="chip" data-action="table" aria-expanded="${s.showTable}">${e(s.showTable ? t("hideTable") : t("showTable"))}</button>
          </div>
        </div>
        ${empty}
        <div id="chart-wrap" class="chart-wrap">
          <div id="chart" tabindex="0" role="group" aria-roledescription="chart" aria-label="${e(chartTitle)}">${hasAny ? this._chartSvg() : ""}</div>
          <div id="tooltip" class="tooltip" aria-live="polite">${hasAny ? this._tooltip() : ""}</div>
        </div>
        <div class="legend">
          <span><i class="sw import"></i>${e(t("imported"))}</span>
          ${d.export_status === "available" ? `<span><i class="sw export"></i>${e(t("exported"))}</span>` : ""}
          <span><i class="sw flagged"></i>${e(t("flaggedLegend"))}</span>
          <span><i class="sw missing"></i>${e(t("missing"))}</span>
        </div>
        ${s.showTable ? this._table() : ""}
      </section>`;
  }

  _chartSvg() {
    const d = this._state.data;
    const width = Math.max(260, this._width);
    const height = this._narrow ? 200 : 260;
    const digits = d.resolution === "interval" ? 2 : 0;
    return renderChart({
      points: d.points,
      resolution: d.resolution,
      mode: this._state.mode,
      width,
      height,
      active: this._state.active,
      label: (p) => this._pointLabel(p),
      fmt: this._fmt(digits),
    });
  }

  _tooltip() {
    const t = this._t;
    const s = this._state;
    const p = s.data?.points?.[s.active];
    if (!p) return "";
    const fmt = this._fmt(3);
    const unitPower = s.data.resolution === "interval" && s.mode === "power";
    const val = (v) =>
      v == null ? e(t("missing")) : `${fmt(unitPower ? v * 4 : v)} ${unitPower ? t("kw") : t("kwh")}`;
    const when =
      s.data.resolution === "interval"
        ? `${formatDateTime(this._lang, p.start)} – ${formatTime(this._lang, p.end)}`
        : s.data.resolution === "month"
          ? formatMonth(this._lang, p.start)
          : formatDay(this._lang, p.start, { dateStyle: "full" });
    const quality =
      s.data.resolution === "interval"
        ? (p.import_q || []).map((q) => s.meters.find((m) => m.entry_id === s.entryId)?.qualities?.[q] || q).join(", ")
        : p.expected
          ? `${this._fmt(1)(p.coverage)} % ${t("coverage").toLowerCase()}${p.flagged ? `, ${t("flagged", { n: p.flagged })}` : ""}`
          : "";
    return `<strong>${e(when)}</strong> · ${e(t("imported"))}: ${val(p.import)}${
      p.export !== undefined ? ` · ${e(t("exported"))}: ${val(p.export)}` : ""
    }${quality ? ` · ${e(quality)}` : ""}`;
  }

  _table() {
    const t = this._t;
    const d = this._state.data;
    const fmt = this._fmt(3);
    const head = d.resolution === "interval" ? t("time") : d.resolution === "day" ? t("date") : t("month");
    const hasExport = d.export_status === "available";
    const rows = d.points
      .map((p) => {
        const label =
          d.resolution === "interval" ? formatDateTime(this._lang, p.end) : this._pointLabel(p, false);
        const q =
          d.resolution === "interval"
            ? (p.import_q || []).join(" ")
            : `${this._fmt(1)(p.coverage)} %`;
        return `<tr><th scope="row">${e(label)}</th><td>${p.import == null ? e(t("missing")) : fmt(p.import)}</td>${
          hasExport ? `<td>${p.export == null ? e(t("missing")) : fmt(p.export)}</td>` : ""
        }<td>${e(q)}</td></tr>`;
      })
      .join("");
    return `<div class="table-wrap"><table><thead><tr><th scope="col">${e(head)}</th><th scope="col">${e(t("imported"))} (${t("kwh")})</th>${
      hasExport ? `<th scope="col">${e(t("exported"))} (${t("kwh")})</th>` : ""
    }<th scope="col">${e(d.resolution === "interval" ? t("quality") : t("coverage"))}</th></tr></thead><tbody>${rows}</tbody></table></div>`;
  }

  _renderChartOnly() {
    const chart = this.shadowRoot.getElementById("chart");
    const tip = this.shadowRoot.getElementById("tooltip");
    if (!chart || !this._state.data) return;
    if (this._state.data.points.some((p) => p.import != null)) {
      chart.innerHTML = this._chartSvg();
      if (tip) tip.innerHTML = this._tooltip();
    }
  }
}

if (!customElements.get("mojelektro-plus-panel")) {
  customElements.define("mojelektro-plus-panel", MojElektroPanel);
}

export { spanDays };
