# Changelog

## 0.1.0

First version.

- Setup in the UI with an API token and meter ID, validated before saving; options, re-authentication and reconfiguration; several meters, duplicates refused.
- Background history download in calendar months (up to two years), resumable after restarts; the last 7 days are re-read on every refresh to pick up late readings and corrections.
- Sensors for the latest interval (energy and delayed average power), the latest complete day, this month and last month, for imported energy and, when the meter reports it, exported energy; plus latest reading, last refresh, data age, coverage and history download status, and a Refresh button.
- Hourly statistics for the Energy dashboard at the time of measurement.
- The Moj Elektro sidebar page: presets and custom ranges, summaries, 15-minute, daily and monthly charts, quality and coverage markers, data table, CSV export, English and Slovenian.
- `mojelektro_plus.refresh_range` action and redacted diagnostics.
