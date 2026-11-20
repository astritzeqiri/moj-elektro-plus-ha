# Releasing

The Home Assistant Marketplace (2026.11+) and HACS show versions from GitHub
**releases** (a full release, not just a tag). Without a release they show
commit hashes.

1. Choose the version (SemVer: features → minor, fixes → patch).
2. Bump it in all of:
   - `custom_components/mojelektro_plus/manifest.json` (`version`)
   - `custom_components/mojelektro_plus/const.py` (`VERSION`; also the panel
     cache-busting key)
   - `frontend/package.json` and `frontend/package-lock.json`
   - `pyproject.toml`
3. Add a `## X.Y.Z` entry at the top of `CHANGELOG.md`.
4. Rebuild the panel: `cd frontend && npm ci && npm run build`, then
   `npm test` and `npm run check`.
5. Run `script/docker-test ruff check .`, `script/docker-test ruff format --check .`
   and `script/docker-test pytest -q`.
6. Commit as `Release X.Y.Z: …` and push `main`. Use the SSH remote: an HTTPS
   token without the `workflow` scope is rejected for changes under
   `.github/workflows/`.
7. Wait for the **Validate** workflow on that commit to pass.
8. Tag and publish:

   ```sh
   git tag -a vX.Y.Z -m "Moj Elektro Plus X.Y.Z" <commit>
   git push origin vX.Y.Z
   gh release create vX.Y.Z --title "X.Y.Z" --notes-file <notes> --verify-tag --latest
   ```

   Use the changelog entry as notes, plus how to update (Marketplace or HACS,
   restart Home Assistant, refresh the browser) and any migrations.
9. Optional, for the HACS default catalog: the repository must be public, have
   a description, topics and issues enabled, pass the HACS action without
   ignores and Hassfest, and have at least one release; then open a PR to
   `hacs/default` (file `integration`).

Storage format changes need a `STORAGE_VERSION`/`STORAGE_MINOR_VERSION` bump
and a migration in `storage.py`. Statistic IDs must not change between
releases; if they ever must, migrate the existing statistics.
