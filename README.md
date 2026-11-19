# Moj Elektro Plus for Home Assistant

A Home Assistant custom integration (HACS) for Slovenian electricity meters
in the **Moj Elektro** service. It downloads 15-minute meter readings,
keeps up to two years of history locally, feeds the **Energy dashboard** at
the correct measurement times and adds a **Moj Elektro** sidebar page with
charts, summaries and CSV export.

Domain: `mojelektro_plus`. It can be installed next to the existing
[`mojelektro`](https://github.com/frlequ/homeassistant-mojelektro)
integration without conflicts (see [NOTICE.md](NOTICE.md)).

> **Delayed data.** Moj Elektro publishes readings with a delay — usually the
> next day, sometimes later. 15-minute granularity does not mean 15-minute
> freshness. Nothing in this integration is "live".

## Features

- Setup entirely in the UI: API token (masked) and meter ID (EIMM, e.g.
  `4-93571`), optional name, history depth (default 12 complete calendar
  months, max 24), refresh interval (default 6 h, min 1 h) and sidebar page.
- Multiple meters (one entry each); duplicates are refused.
- Options, re-authentication and reconfiguration flows.
- Background history download in calendar-month batches (≤ 35 days per
  request), with progress, resumable after restarts.
- Every refresh re-reads the last 7 days to pick up late readings and
  corrections; revisions are merged idempotently by UTC interval end.
- Imported and — when the meter provides it — exported energy. A meter that
  does not provide an export register shows "not provided", never zero.
- Days and months use **Europe/Ljubljana**, whatever timezone Home Assistant
  runs in; DST days have 92 or 100 intervals; an interval ending at midnight
  belongs to the previous day.
- Quality flags are kept and shown; missing intervals stay missing (never
  zero) and partial periods are labelled with their coverage.

## Installation (HACS custom repository)

1. HACS → ⋮ → **Custom repositories** → add
   `https://github.com/astritzeqiri/moj-elektro-plus-ha`, type **Integration**.
2. Install **Moj Elektro Plus** and restart Home Assistant.
3. Settings → Devices & services → **Add integration** → *Moj Elektro Plus*.

Manual install: copy `custom_components/mojelektro_plus/` into your
`config/custom_components/` and restart.

Requires Home Assistant 2026.3 or newer.

## Setup

1. Sign in at <https://mojelektro.si>, open **Moj profil → Kreiraj žeton**
   and create an API token.
2. Find your meter identifier (EIMM, e.g. `4-93571`) under **Merilna mesta**.
3. Enter both in the setup form. The integration checks the token, the meter
   and read access to readings before saving. Errors are reported as:
   invalid token, meter not accessible, invalid meter ID, timeout, rate
   limited, or service error.

**About the token:** it is stored in Home Assistant's configuration storage
(`.storage/core.config_entries`) like other integrations' credentials. Home
Assistant does not encrypt that file, so protect your backups. The token is
only used by the backend; it is never sent to the browser, never written to
entity attributes, logs or diagnostics (diagnostics redact it).

To change the token: Devices & services → Moj Elektro Plus → ⋮ →
**Reconfigure**. When a token stops working, Home Assistant asks for a new
one automatically (re-authentication).

## Entities (per meter)

| Entity | Notes |
| --- | --- |
| Latest interval imported energy | kWh of the most recent available 15-minute interval |
| Latest interval average import power (delayed) | interval kWh × 4 — an average, not instantaneous power |
| Latest complete day imported energy | the newest day with all expected intervals |
| This month imported energy (partial) | with coverage attributes |
| Last month imported energy | `complete` attribute shows whether all intervals are present |
| Export equivalents | only created once the API returns an export register |
| Latest available reading | timestamp of the newest interval end |
| Last successful refresh, data age, this month's coverage, history download | diagnostics |
| Refresh (button) | re-reads the recent window now |

None of the energy sensors has a state class. That is deliberate: Home
Assistant would otherwise record their changes at the moment data *arrives*
and draw yesterday's consumption as a spike today. Long-term history comes
from external statistics instead (next section).

## Energy dashboard

The integration imports hourly external statistics, placed at the hours the
energy was measured:

- `mojelektro_plus:<meter>_energy_consumption` (grid import)
- `mojelektro_plus:<meter>_energy_return` (grid export, when provided)

Settings → Dashboards → **Energy** → *Electricity grid* → add a grid
connection and choose these statistics ("… imported energy" / "… exported
energy"). Home Assistant does not allow attaching a price entity or fixed
price to external statistics, and this integration does not calculate costs
(see *Costs*).

How sums work: cumulative sums are recomputed from stored intervals; when a
late reading or correction arrives, every hour from the earliest change on is
re-written (the recorder upserts by hour), so restarts and re-downloads never
duplicate consumption. The Energy dashboard groups days by Home Assistant's
own timezone, while the sidebar page uses Europe/Ljubljana days.

## The Moj Elektro sidebar page

Enabled by default (option *Show the Moj Elektro sidebar page*). One page
serves all meters; it is removed when the last meter with the option enabled
is unloaded. It opens on the **latest day with data** and offers:

- meter selector; presets for latest day, last 7 / 30 days, this month,
  previous month and last 12 months, or a custom range;
- imported/exported totals, daily average (complete days only), peak
  15-minute average demand, coverage and quality-flag counts;
- 15-minute energy or average-power chart for up to 3 days, daily bars up to
  92 days, monthly bars beyond; missing data and flagged readings are marked;
- a data table (also for keyboard and screen-reader users);
- latest measurement, last refresh, delayed-data notice, history-download
  progress, refresh and re-download (administrators), CSV export.

Aggregation happens on the server, so long ranges send monthly or daily
points, not every interval. The CSV contains UTC and Europe/Ljubljana
timestamps, kWh (and kW averages), per-interval status (`ok`, `flagged`,
`missing`) and quality codes.

All data access goes through Home Assistant's authenticated WebSocket API.
Any signed-in user can view data; refreshing and re-downloading require an
administrator. English and Slovenian are included.

## History limits

- The API serves at most two years of history and at most 35 days per
  request. The default history is 12 complete calendar months plus the
  current month; up to 24 months can be chosen.
- Local storage is bounded (about 26 months per meter).
- To re-download a period (for example after corrections), use the page's
  *Re-download this period* or the action `mojelektro_plus.refresh_range`.

## Costs

Not included. Supplier tariffs, network charges (omrežnina), taxes and
billing arrangements are separate inputs that are not part of meter data, so
euro amounts cannot be derived from consumption alone. This version focuses on
accurate measurements.

## Removal

Settings → Devices & services → Moj Elektro Plus → ⋮ → **Delete**. This
removes the entities, the locally stored intervals and this meter's imported
statistics (remove the source from the Energy dashboard first). The sidebar
page disappears with the last entry. Then uninstall the repository in HACS
and restart.

## Troubleshooting

- *Data age* is normally 10–40 hours. Larger values usually mean Moj Elektro
  has not published new readings yet; refreshing more often does not help.
- Diagnostics (device page → Download diagnostics) are redacted and safe to
  share in issues.

## Development

See [docs/DEVELOPMENT.md](docs/DEVELOPMENT.md) and
[docs/RELEASING.md](docs/RELEASING.md).

## License

MIT — see [LICENSE](LICENSE) and [NOTICE.md](NOTICE.md). Not affiliated with
Informatika d.o.o. or the Slovenian distribution companies.
