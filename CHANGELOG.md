# Changelog

## 0.2.0

A clearer Moj Elektro page.

- The period you are looking at is now the page heading ("Thu, 19 November 2026", "October 2026"), with ‹ › arrows to step back and forward by the same length (a day, 7 or 30 days, or a calendar month). Stepping never goes past the newest reading or before the two-year history limit.
- One summary instead of five separate cards: the imported total leads, with a Complete or Partial badge and the number of readings; exported energy, peak 15-minute demand and, for longer periods, the daily average sit beside it. Figures keep two decimals.
- The chart only reserves room below zero when energy was actually exported, so meters that report zero export get a full-height chart.
- Presets sit in one row (one swipeable row on phones); Custom opens the date fields only when needed. The meter picker only shows with more than one meter.
- The latest measurement shows under the heading; the delayed-data explanation, last refresh, history status and re-download sit in a quiet section at the bottom. Refresh and Export CSV are next to the heading.
- Material Design icons, consistent hover and focus states, aligned numerals and theme-coloured text selection.
- README: tip that the Energy dashboard opens on today, which stays empty until Moj Elektro publishes the day.

## 0.1.0

First version.

- Setup in the UI with an API token and meter ID, validated before saving; options, re-authentication and reconfiguration; several meters, duplicates refused.
- Background history download in calendar months (up to two years), resumable after restarts; the last 7 days are re-read on every refresh to pick up late readings and corrections.
- Sensors for the latest interval (energy and delayed average power), the latest complete day, this month and last month, for imported energy and, when the meter reports it, exported energy; plus latest reading, last refresh, data age, coverage and history download status, and a Refresh button.
- Hourly statistics for the Energy dashboard at the time of measurement.
- The Moj Elektro sidebar page: presets and custom ranges, summaries, 15-minute, daily and monthly charts, quality and coverage markers, data table, CSV export, English and Slovenian.
- `mojelektro_plus.refresh_range` action and redacted diagnostics.
