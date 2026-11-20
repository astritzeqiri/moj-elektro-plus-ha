# Working on Moj Elektro Plus

This guide applies to the `moj-elektro-plus-ha` repository. Follow the user's task and existing authorization; reading this file is not a request to commit, push or publish a release.

## Product and package layout

- Repository: `https://github.com/astritzeqiri/moj-elektro-plus-ha` (public), branch `main`. Remote `origin` uses SSH (`git@github.com:astritzeqiri/moj-elektro-plus-ha.git`).
- One Home Assistant custom integration, domain **`mojelektro_plus`**, installed through the Home Assistant **Marketplace** (built-in HACS since HA 2026.11) or HACS on older versions. It must never reuse the domain `mojelektro`, which belongs to the older community integration.
- Everything Home Assistant loads lives in `custom_components/mojelektro_plus/`, including the **built** sidebar page `frontend/mojelektro-panel.js` and the `brand/` icons. Marketplace/HACS users never run Node.
- Minimum Home Assistant: **2026.3.0** (`hacs.json`). Runtime checks use Core **2026.11.0**.

| Path | Role |
| --- | --- |
| `custom_components/mojelektro_plus/api.py` | Async Moj Elektro client: timeouts, retries, Retry-After, error mapping |
| `timeutil.py` | UTC identity, Europe/Ljubljana days and months, DST, ≤35-day batches |
| `data.py` | Interval storage in UTC-day chunks, merge/dedupe, period totals |
| `storage.py` | Versioned `Store` per config entry |
| `coordinator.py` | Recent-window refresh, background backfill, range refresh, snapshot |
| `statistics.py` | External statistics for the Energy dashboard |
| `views.py`, `websocket.py` | Server-side aggregation, CSV, authenticated WebSocket commands |
| `panel.py` | Shared sidebar panel registration |
| `sensor.py`, `button.py`, `config_flow.py`, `diagnostics.py` | Entities, flows, redacted diagnostics |
| `frontend/` (repo root) | **Source** of the sidebar page, its tests and `build.mjs` |
| `tests/` | pytest suite with a fake API (`tests/fake_api.py`); never calls the real API |
| `script/docker-test` | Runs Python tests/lint in a `python:3.14` container |
| `script/dev-ha`, `script/dev/mojelektro_dev_fake/` | Local dev Home Assistant and its optional synthetic-data helper |
| `branding/generate_icons.py` | Regenerates the brand icons |

## Rules that must not regress

- **The token stays on the backend.** It is only sent as `X-API-TOKEN`. Never put it in WebSocket responses, entity attributes, logs, exceptions, diagnostics, fixtures, screenshots or commits. Do not claim it is encrypted at rest; Home Assistant does not encrypt config entries.
- **Data is delayed.** Never call readings live. Average power is interval kWh × 4 and labelled delayed.
- **Identity is the UTC interval end; aggregation is Europe/Ljubljana**, independent of the HA timezone. An interval ending at midnight belongs to the previous day. DST days have 92 or 100 intervals.
- **Missing is not zero.** A reading without a value never erases a stored value. No export block means "not provided", not zero export. Partial periods show coverage.
- **API limits** (confirmed against the live service): a ReadingType `option` is required, at most 35 days per request, at most two years back, `endTime` is exclusive, timestamps mark interval ends.
- **Energy sensors have no state class**; the Energy dashboard uses external statistics placed at measurement time. Statistic IDs (`mojelektro_plus:<meter>_energy_consumption` / `_energy_return`) must never change between releases.
- **Storage format changes** need a `STORAGE_VERSION`/`STORAGE_MINOR_VERSION` bump and a migration in `storage.py`. Existing history must survive upgrades.
- **No costs** are calculated. HA also refuses prices on external statistics.
- The sidebar page talks only to `mojelektro_plus/*` WebSocket commands. Reads need a signed-in user; refresh and backfill need an administrator.
- Keep translations complete in `strings.json`, `translations/en.json`, `translations/sl.json` and `frontend/src/i18n.js` (a test checks the frontend keys match).

## Making a change

Python, from the repository root (Docker; the local macOS Python 3.14 is an Intel build that cannot load the test wheels):

```sh
script/docker-test ruff check .
script/docker-test ruff format --check .
script/docker-test pytest -q --timeout=120
```

Frontend, from `frontend/`:

```sh
npm ci            # only when dependencies need installing
npm test          # vitest + happy-dom
npm run build     # writes custom_components/mojelektro_plus/frontend/mojelektro-panel.js
npm run check     # fails if the committed bundle differs from a fresh build
```

Always rebuild after editing `frontend/src/` and commit the bundle with its source; CI runs `npm run check`.

Manifest validation with the official image (same as CI's Hassfest job):

```sh
docker run --rm -v "$PWD/custom_components/mojelektro_plus":/github/workspace/custom_components/mojelektro_plus:ro ghcr.io/home-assistant/hassfest
```

## Local Home Assistant for testing

`script/dev-ha start|stop|restart|recreate|logs` runs **its own** container, `mojelektro-plus-homeassistant`, at `http://127.0.0.1:18124`, pinned to the same 2026.11.0 image digest as the 3D Rooms test instance. It is separate from the 3D Rooms singleton (`three-d-rooms-homeassistant`, port 18123); never start, stop or reconfigure that one from this repo, and never create more Moj Elektro containers.

- The integration folder is mounted **read-only** from this checkout, so a restart picks up code changes. The panel URL carries the bundle's mtime, so **restart after every frontend build** (`script/dev-ha restart`), then hard-refresh the browser.
- Config, database and logins live in ignored `.local/homeassistant/`. The dev login is `devadmin`; its generated password and refresh token are in `.local/homeassistant/session.json`. Never print them in chat or commit them.
- The instance talks to the **real** Moj Elektro API by default. The user has added their own meter there with their own token; leave that entry, its data and the Energy dashboard configuration alone unless asked.
- `MOJELEKTRO_DEV_FAKE=1 script/dev-ha recreate` additionally mounts the synthetic-data helper (any token except `invalid`; meters `4-93571` with export and `9-12345`). Delete synthetic entries before switching back with `script/dev-ha recreate`, so test data never mixes with real data. Never install the helper anywhere else.
- The instance's timezone is **Europe/Ljubljana**, so Energy dashboard days match the sidebar page.
- This instance is never the user's production Home Assistant. Do not touch production unless explicitly asked.

## Releasing

Releases are what the Marketplace and HACS show as versions. Without a GitHub release they show commit hashes. Publish only when the user asks.

1. Choose the version (SemVer: new features → minor, fixes only → patch).
2. Bump it in **all** of these:
   - `custom_components/mojelektro_plus/manifest.json` → `version`
   - `custom_components/mojelektro_plus/const.py` → `VERSION` (also the panel cache key)
   - `frontend/package.json` and `frontend/package-lock.json` (top-level and `packages[""]`)
   - `pyproject.toml`
3. Add a `## X.Y.Z` entry at the top of `CHANGELOG.md`, written for users.
4. Rebuild and check: `npm run build`, `npm test` and `npm run check` in `frontend/`; ruff and pytest via `script/docker-test`; hassfest via Docker.
5. Commit as `Release X.Y.Z: <summary>`, ending with the attribution line, and push `main`.
6. **Push over SSH.** The stored HTTPS credential and the `gh` token lack the `workflow` scope, so HTTPS pushes that touch `.github/workflows/` are rejected. The `origin` remote already uses SSH; if needed: `GIT_SSH_COMMAND="ssh -o BatchMode=yes" git push`.
7. Wait for the **Validate** workflow on that commit to pass (HACS, Hassfest, Python, Frontend), e.g. `gh run watch <run-id> -R astritzeqiri/moj-elektro-plus-ha --exit-status`.
8. Tag and publish:

   ```sh
   git tag -a vX.Y.Z -m "Moj Elektro Plus X.Y.Z" <commit>
   git push origin vX.Y.Z
   gh release create vX.Y.Z -R astritzeqiri/moj-elektro-plus-ha --title "X.Y.Z" --notes-file <notes> --verify-tag --latest
   ```

   Notes: the changelog entry plus a short update line (Marketplace or HACS → update → restart Home Assistant → refresh the browser).
9. Confirm `gh api repos/astritzeqiri/moj-elektro-plus-ha/releases/latest` returns the new tag.

The local dev instance runs the working tree, not the release; it already reflects the release once the release commit is checked out.

Releases so far: `v0.1.0` (first version), `v0.2.0` (clearer sidebar page).

## GitHub repository

- The HACS check needs the repository **description** and **topics** (`energy`, `hacs`, `home-assistant`, `homeassistant-integration`, `mojelektro`, `slovenia`). Keep them set.
- HACS reports a non-blocking warning that the manifest has no `categories`. Only add one after confirming the HACS action accepts its value; an unknown category fails the check.
- Dependabot opens PRs for GitHub Actions and frontend dependencies. Their CI ran before the repo had a description and topics, so the HACS job shows as failed there; re-run before judging them. Review major upgrades (e.g. vitest, happy-dom) for real failures, rebuild the bundle when frontend tooling changes, and never merge one without the user asking.
- HACS default-catalog submission (optional, user decision): public repo, description, topics, issues enabled, passing HACS action without ignores and Hassfest, at least one release, then a PR to `hacs/default`.

## Before you finish

- `git status --short`: no `.local/`, `node_modules/`, caches or secrets staged. Scan staged files for the dev password or any token before committing.
- Report which checks ran and what could not be verified (for example, real-API behaviour, or the Marketplace install step itself).
