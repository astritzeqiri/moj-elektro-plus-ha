// @vitest-environment happy-dom
import { afterEach, beforeEach, describe, expect, it, vi } from "vitest";
import "../src/panel.js";
import { presetRange, isValidDate, ljubljanaToday, stepRange } from "../src/dates.js";
import { renderChart } from "../src/chart.js";
import { translator, STRINGS } from "../src/i18n.js";

const TOKEN = "never-visible-token";

function meter(id, title, extra = {}) {
  return {
    entry_id: id,
    title,
    meter_id: id === "a" ? "9-12345" : "4-93571",
    export_status: "not_provided",
    latest_reading: "2026-04-09T22:00:00+00:00",
    latest_day: "2026-04-09",
    last_success: "2026-04-10T06:00:00+00:00",
    backfill: { state: "complete", done: 2, total: 2, error: null },
    job: null,
    qualities: { "TEST.ESTIMATED": "Estimated" },
    earliest_allowed: "2024-04-11",
    ...extra,
  };
}

function intervalPoints(n = 96, missingAt = 3) {
  return Array.from({ length: n }, (_, i) => ({
    start: new Date(Date.UTC(2026, 3, 8, 22, i * 15)).toISOString(),
    end: new Date(Date.UTC(2026, 3, 8, 22, (i + 1) * 15)).toISOString(),
    import: i === missingAt ? null : 0.1 + (i % 4) * 0.05,
    import_q: i === 5 ? ["TEST.ESTIMATED"] : [],
  }));
}

function dataFor(msg) {
  const span =
    (Date.parse(msg.end) - Date.parse(msg.start)) / 86400000 + 1;
  const resolution = span <= 3 ? "interval" : span <= 92 ? "day" : "month";
  const points =
    resolution === "interval"
      ? intervalPoints()
      : Array.from({ length: Math.min(span, 31) }, (_, i) => ({
          start: `2026-03-${String(i + 1).padStart(2, "0")}`,
          end: `2026-03-${String(i + 1).padStart(2, "0")}`,
          import: 9.5,
          present: 96,
          expected: 96,
          coverage: 100,
          complete: true,
          flagged: 0,
        }));
  return {
    entry_id: msg.entry_id,
    start: msg.start,
    end: msg.end,
    resolution,
    timezone: "Europe/Ljubljana",
    export_status: "not_provided",
    summary: {
      import: { total: 12.34, present: 95, expected: 96, coverage: 98.96, complete: false, flagged: 1 },
      export: null,
      days: span,
      complete_days: 0,
      daily_average: null,
      peak: { power_kw: 1.2, energy_kwh: 0.3, interval_start: "2026-04-09T05:00:00+00:00", interval_end: "2026-04-09T05:15:00+00:00" },
    },
    points,
  };
}

function makeHass({ meters = [meter("a", "House"), meter("b", "Cottage")], admin = true, fail = {} } = {}) {
  const calls = [];
  const subscribers = [];
  const hass = {
    language: "en",
    locale: { language: "en" },
    connected: true,
    user: { is_admin: admin },
    callWS: vi.fn(async (msg) => {
      calls.push(msg);
      const kind = msg.type.split("/")[1];
      if (fail[kind]) throw new Error(fail[kind]);
      if (kind === "meters") return { meters };
      if (kind === "data") return dataFor(msg);
      if (kind === "csv") return { filename: "x.csv", csv: "a,b\n" };
      if (kind === "refresh" || kind === "backfill") return { started: true };
      throw new Error(`unexpected ${msg.type}`);
    }),
    connection: {
      subscribeMessage: vi.fn(async (cb) => {
        subscribers.push(cb);
        return () => {};
      }),
    },
  };
  return { hass, calls, subscribers };
}

const flush = () => new Promise((r) => setTimeout(r, 0));

async function mount(opts) {
  const ctx = makeHass(opts);
  const el = document.createElement("mojelektro-plus-panel");
  document.body.appendChild(el);
  el.narrow = opts?.narrow ?? false;
  el.hass = ctx.hass;
  for (let i = 0; i < 5; i++) await flush();
  return { el, root: el.shadowRoot, ...ctx };
}

beforeEach(() => {
  try {
    localStorage.clear();
  } catch {}
});
afterEach(() => {
  document.body.innerHTML = "";
});

describe("panel loading", () => {
  it("shows the latest available day first, not an empty today", async () => {
    const { root, calls } = await mount();
    const data = calls.filter((c) => c.type === "mojelektro_plus/data");
    expect(data[0]).toMatchObject({ entry_id: "a", start: "2026-04-09", end: "2026-04-09" });
    expect(root.textContent).toContain("Delayed data");
    expect(root.textContent).toContain("15-minute values");
    expect(root.querySelectorAll("svg rect.bar.import").length).toBe(95);
    expect(root.querySelectorAll("svg rect.missing").length).toBe(1);
    expect(root.querySelectorAll("svg rect.flagged").length).toBe(1);
    expect(root.textContent).toContain("Partial period");
    expect(root.textContent).toContain("Not provided for this meter");
    expect(root.innerHTML).not.toContain(TOKEN);
  });

  it("shows a loading state before data arrives", () => {
    const { hass } = makeHass();
    hass.callWS = vi.fn(() => new Promise(() => {}));
    const el = document.createElement("mojelektro-plus-panel");
    document.body.appendChild(el);
    el.hass = hass;
    expect(el.shadowRoot.textContent).toContain("Loading");
  });

  it("explains when no meters are configured", async () => {
    const { root } = await mount({ meters: [] });
    expect(root.textContent).toContain("No meters are set up");
  });

  it("shows an error with retry when meters cannot load", async () => {
    const { root, hass } = await mount({ fail: { meters: "boom" } });
    expect(root.querySelector("[role=alert]").textContent).toContain("boom");
    hass.callWS.mockImplementation(async (msg) =>
      msg.type.endsWith("meters") ? { meters: [meter("a", "House")] } : dataFor(msg),
    );
    root.querySelector("[data-action=retry]").click();
    for (let i = 0; i < 5; i++) await flush();
    expect(root.querySelector("svg")).not.toBeNull();
  });

  it("waits and retries while Home Assistant is still starting", async () => {
    vi.useFakeTimers();
    const { hass } = makeHass();
    let ready = false;
    const real = hass.callWS.getMockImplementation();
    hass.callWS.mockImplementation(async (msg) => {
      if (!ready) throw Object.assign(new Error("Unknown command."), { code: "unknown_command" });
      return real(msg);
    });
    const el = document.createElement("mojelektro-plus-panel");
    document.body.appendChild(el);
    el.hass = hass;
    await vi.advanceTimersByTimeAsync(10);
    expect(el.shadowRoot.textContent).toContain("Loading");
    expect(el.shadowRoot.querySelector("[role=alert]")).toBeNull();
    ready = true;
    await vi.advanceTimersByTimeAsync(3100);
    vi.useRealTimers();
    for (let i = 0; i < 5; i++) await flush();
    expect(el.shadowRoot.querySelector("svg")).not.toBeNull();
  });

  it("shows data errors without losing the page", async () => {
    const { root } = await mount({ fail: { data: "Choose at most 800 days." } });
    expect(root.querySelector("[role=alert]").textContent).toContain("800 days");
    expect(root.querySelector("#meter")).not.toBeNull();
  });

  it("shows an offline banner", async () => {
    const { el, root, hass } = await mount();
    el.hass = { ...hass, connected: false };
    expect(root.textContent).toContain("offline");
  });
});

describe("interaction", () => {
  it("switches meters and remembers the choice", async () => {
    const { root, calls } = await mount();
    const select = root.querySelector("#meter");
    select.value = "b";
    select.dispatchEvent(new Event("change", { bubbles: true }));
    await flush();
    const last = calls.filter((c) => c.type.endsWith("/data")).at(-1);
    expect(last.entry_id).toBe("b");
    expect(localStorage.getItem("mojelektro_plus.selected_meter")).toBe("b");
  });

  it("applies presets and custom ranges", async () => {
    const { root, calls } = await mount();
    root.querySelector('[data-preset="last30"]').click();
    await flush();
    let last = calls.filter((c) => c.type.endsWith("/data")).at(-1);
    expect(last).toMatchObject({ start: "2026-03-11", end: "2026-04-09" });
    expect(root.textContent).toContain("Daily totals");

    root.querySelector("[data-action=custom]").click();
    expect(root.querySelector("#custom-fields").hidden).toBe(false);
    root.querySelector("#start").value = "2026-03-01";
    root.querySelector("#end").value = "2026-03-05";
    root.querySelector("[data-action=apply-range]").click();
    await flush();
    last = calls.filter((c) => c.type.endsWith("/data")).at(-1);
    expect(last).toMatchObject({ start: "2026-03-01", end: "2026-03-05" });
    expect(root.querySelector('[data-preset="last30"]').getAttribute("aria-pressed")).toBe("false");
  });

  it("rejects an invalid custom range without calling the server", async () => {
    const { root, calls } = await mount();
    const before = calls.length;
    root.querySelector("#start").value = "2026-03-09";
    root.querySelector("#end").value = "2026-03-01";
    root.querySelector("[data-action=apply-range]").click();
    await flush();
    expect(calls.length).toBe(before);
  });

  it("supports keyboard navigation of the chart", async () => {
    const { root } = await mount();
    const chart = root.querySelector("#chart");
    chart.dispatchEvent(new KeyboardEvent("keydown", { key: "End", bubbles: true }));
    expect(root.querySelector("#tooltip").textContent).toMatch(/Imported/);
    chart.dispatchEvent(new KeyboardEvent("keydown", { key: "Home", bubbles: true }));
    chart.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    chart.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    chart.dispatchEvent(new KeyboardEvent("keydown", { key: "ArrowRight", bubbles: true }));
    expect(root.querySelector("#tooltip").textContent).toContain("Missing");
  });

  it("toggles power mode and the accessible table", async () => {
    const { root } = await mount();
    root.querySelector('[data-mode="power"]').click();
    expect(root.querySelector('[data-mode="power"]').getAttribute("aria-pressed")).toBe("true");
    root.querySelector("[data-action=table]").click();
    expect(root.querySelectorAll("tbody tr").length).toBe(96);
    expect(root.querySelector("tbody").textContent).toContain("Missing");
  });

  it("refreshes as admin and hides refresh for other users", async () => {
    const admin = await mount();
    admin.root.querySelector("[data-action=refresh]").click();
    await flush();
    expect(admin.calls.some((c) => c.type === "mojelektro_plus/refresh")).toBe(true);
    document.body.innerHTML = "";
    const user = await mount({ admin: false });
    expect(user.root.querySelector("[data-action=refresh]")).toBeNull();
    expect(user.root.textContent).toContain("Only administrators");
  });

  it("re-downloads the selected range", async () => {
    const { root, calls } = await mount();
    root.querySelector("[data-action=refresh-range]").click();
    await flush();
    expect(calls.find((c) => c.type.endsWith("/refresh"))).toMatchObject({
      start: "2026-04-09",
      end: "2026-04-09",
    });
  });

  it("exports CSV for the current range", async () => {
    globalThis.URL.createObjectURL = vi.fn(() => "blob:x");
    globalThis.URL.revokeObjectURL = vi.fn();
    const { root, calls } = await mount();
    root.querySelector("[data-action=csv]").click();
    await flush();
    expect(calls.find((c) => c.type.endsWith("/csv"))).toMatchObject({
      entry_id: "a",
      start: "2026-04-09",
      resolution: "interval",
    });
  });

  it("reloads when the server announces new data", async () => {
    const { calls, subscribers } = await mount();
    const before = calls.length;
    vi.useFakeTimers();
    subscribers[0]({ entry_id: "a" });
    vi.advanceTimersByTime(1000);
    vi.useRealTimers();
    for (let i = 0; i < 5; i++) await flush();
    expect(calls.length).toBeGreaterThan(before);
  });

  it("shows backfill progress and resume", async () => {
    const { root } = await mount({
      meters: [meter("a", "House", { job: { kind: "backfill", done: 3, total: 12 } })],
    });
    expect(root.textContent).toContain("Downloading month 4 of 12");
    document.body.innerHTML = "";
    const failed = await mount({
      meters: [meter("a", "House", { backfill: { state: "error", error: "RateLimited", done: 1, total: 3 } })],
    });
    expect(failed.root.textContent).toContain("RateLimited");
    failed.root.querySelector("[data-action=backfill]").click();
    await flush();
    expect(failed.calls.some((c) => c.type.endsWith("/backfill"))).toBe(true);
  });

  it("renders a menu button on narrow screens", async () => {
    const { root } = await mount({ narrow: true });
    expect(root.querySelector("[data-action=menu]")).not.toBeNull();
  });
});

describe("period stepping", () => {
  it("steps day by day and never past the latest data", async () => {
    const { root, calls } = await mount();
    expect(root.querySelector("#period-heading").textContent).toContain("2026");
    const next = root.querySelector('[data-action=step][data-dir="1"]');
    expect(next.disabled).toBe(true);
    root.querySelector('[data-action=step][data-dir="-1"]').click();
    await flush();
    const last = calls.filter((c) => c.type.endsWith("/data")).at(-1);
    expect(last).toMatchObject({ start: "2026-04-08", end: "2026-04-08" });
    expect(root.querySelector('[data-action=step][data-dir="1"]').disabled).toBe(false);
  });

  it("steps whole calendar months for month presets", async () => {
    const { root, calls } = await mount();
    root.querySelector('[data-preset="prevMonth"]').click();
    await flush();
    root.querySelector('[data-action=step][data-dir="-1"]').click();
    await flush();
    const last = calls.filter((c) => c.type.endsWith("/data")).at(-1);
    const months = last.end.slice(0, 7);
    expect(last.start.endsWith("-01")).toBe(true);
    expect(last.start.slice(0, 7)).toBe(months);
  });
});

describe("helpers", () => {
  it("resolves presets from the latest available day", () => {
    expect(presetRange("latest", "2026-04-09", "2026-04-10")).toEqual({ start: "2026-04-09", end: "2026-04-09" });
    expect(presetRange("last7", "2026-04-09", "2026-04-10")).toEqual({ start: "2026-04-03", end: "2026-04-09" });
    expect(presetRange("thisMonth", "2026-04-09", "2026-04-10")).toEqual({ start: "2026-04-01", end: "2026-04-10" });
    expect(presetRange("prevMonth", "2026-04-09", "2026-04-10")).toEqual({ start: "2026-03-01", end: "2026-03-31" });
    expect(presetRange("last12", "2026-04-09", "2026-04-10")).toEqual({ start: "2025-05-01", end: "2026-04-10" });
    expect(presetRange("latest", null, "2026-01-01")).toEqual({ start: "2025-12-31", end: "2025-12-31" });
  });

  it("steps ranges by day span and by calendar month", () => {
    expect(stepRange("2026-04-03", "2026-04-09", { unit: "day", n: 7 }, -1, "2026-04-09")).toEqual({ start: "2026-03-27", end: "2026-04-02" });
    expect(stepRange("2026-03-27", "2026-04-02", { unit: "day", n: 7 }, 1, "2026-04-05")).toEqual({ start: "2026-03-30", end: "2026-04-05" });
    expect(stepRange("2026-04-01", "2026-04-10", { unit: "month", n: 1 }, -1, "2026-04-10")).toEqual({ start: "2026-03-01", end: "2026-03-31" });
    expect(stepRange("2026-02-01", "2026-02-28", { unit: "month", n: 1 }, 1, "2026-04-10")).toEqual({ start: "2026-03-01", end: "2026-03-31" });
    expect(stepRange("2026-03-01", "2026-03-31", { unit: "month", n: 1 }, 1, "2026-04-10")).toEqual({ start: "2026-04-01", end: "2026-04-10" });
  });

  it("validates dates and computes Ljubljana today", () => {
    expect(isValidDate("2026-02-29")).toBe(false);
    expect(isValidDate("2028-02-29")).toBe(true);
    expect(ljubljanaToday(new Date("2026-03-31T22:30:00Z"))).toBe("2026-04-01");
  });

  it("draws missing values as markers, not zero bars", () => {
    const svg = renderChart({
      points: [{ import: 1 }, { import: null }, { import: 0 }],
      resolution: "day",
      mode: "energy",
      width: 300,
      height: 200,
      active: null,
      label: () => "",
      fmt: String,
    });
    expect((svg.match(/class="missing/g) || []).length).toBe(1);
    expect((svg.match(/class="bar import/g) || []).length).toBe(2);
  });

  it("has every English key translated to Slovenian", () => {
    const keys = (o, p = "") =>
      Object.entries(o).flatMap(([k, v]) => (typeof v === "object" ? keys(v, `${p}${k}.`) : [`${p}${k}`]));
    expect(keys(STRINGS.sl).sort()).toEqual(keys(STRINGS.en).sort());
    expect(translator("sl")("presets.latest")).toBe("Zadnji dan");
  });
});
