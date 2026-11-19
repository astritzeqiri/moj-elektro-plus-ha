# Releasing

HACS installs from GitHub releases (a full release, not just a tag).

1. Make sure `main` is green (HACS, Hassfest, Python and Frontend jobs).
2. Bump the version in **both**
   `custom_components/mojelektro_plus/manifest.json` (`version`) and
   `custom_components/mojelektro_plus/const.py` (`VERSION`; also the panel
   cache-busting key), plus `frontend/package.json` and `pyproject.toml`.
3. Rebuild the panel: `cd frontend && npm ci && npm run build`, then
   `npm run check`.
4. Run `script/docker-test pytest -q` and `cd frontend && npm test`.
5. Commit, then tag `vX.Y.Z` and push the tag.
6. Create a GitHub release for the tag with release notes (what changed,
   any storage or statistics migrations, minimum Home Assistant version).
7. Optional, for the HACS default list: the repository must be public, have
   a description, topics and issues enabled, pass the HACS action without
   ignores and Hassfest, and have at least one release; then open a PR to
   `hacs/default` (file `integration`).

Storage format changes need a `STORAGE_VERSION`/`STORAGE_MINOR_VERSION` bump
and a migration in `storage.py`. Statistic IDs must not change between
releases; if they ever must, migrate the existing statistics.
