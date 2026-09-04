# OVERHEATLENS — DELEGATION HANDOFF PROMPT

Copy the section between the `====` markers below and paste it to another AI
coding worker (Claude Code, Codex, Windsurf, Cursor agent, …). It is
self-contained: context, current state, environment warnings, a full todo list
with file paths, validation commands and tests required, and a definition of
done. Work IN PLACE in the repository — do not build a disconnected copy.

Repository (authoritative, work here):
`/Users/mohamedali/Library/CloudStorage/OneDrive-LeedsBeckettUniversity/Work/GITHUB REPO/OverheatLens`

If the worker has no filesystem access to OneDrive, copy the whole folder to a
local disk (e.g. `/tmp/OverheatLens-work` or `~/OverheatLens-work`), work there,
and copy changed files back. This is REQUIRED to run the web test suite (see
Environment warnings).

---

==== BEGIN PROMPT — PASTE TO THE WORKER ====

# OverheatLens — finish the remaining work

You are continuing a large rebuild of **OverheatLens**, an open local-first
research platform for domestic-overheating assessment: weather-file QC →
building-model readiness → EnergyPlus simulation → versioned standards
(TM59:2017/2026, Part O dynamic, TM52) → comfort analytics → mitigation →
reproducible evidence. It is a monorepo: `packages/overheatlens-core`
(authoritative Python science), `apps/api` (FastAPI), `apps/web`
(React 19 + TypeScript + ECharts, Neo-Brutalist design system), `data/`
(archetypes, uploads, runs), `fixtures/`, `scripts/`, `docs/`.

## IMPORTANT — environment warnings (read first, they will bite you)

1. **The repo lives on OneDrive Files-On-Demand.** Files are frequently evicted
   and reads can block for 30s–minutes or fail with `Operation timed out
   (os error 60)`. If a read/import/build hangs, it is usually OneDrive, not
   your code. Mitigations: wait, retry, or work on a local-disk copy.
2. **Vitest (web tests) will NOT start on this machine** — it hangs before test
   discovery with every pool backend (`threads`, `forks`, `vmThreads`), even for
   a trivial probe on local disk under Node 24/26. This is environmental and
   pre-existing. To actually run web tests, copy `apps/web` to a local disk
   (keep `node_modules` — symlink or copy it), or run in CI. `tsc -b` and
   `vite build` DO work in place.
3. **Disk space was near-full (as low as 3.5 GiB free on `/`)** during the
   session; it may recover. Check `df -h /` first. If very low, builds can fail
   with file-read timeouts on node_modules because evicted on-demand files
   cannot be re-downloaded. A known fix if `vite build` says
   `Could not load node_modules/zrender/lib/mixin/Draggable.js`: the file is
   evicted/unreadable; delete it and re-copy from a fresh `npm pack zrender@6.1.0`
   (`npm pack zrender@6.1.0 --pack-destination /tmp/zr && tar -xzf /tmp/zr/zrender-6.1.0.tgz -C /tmp/zr && cp /tmp/zr/package/lib/mixin/Draggable.js node_modules/zrender/lib/mixin/Draggable.js`).
   Other evicted files may need the same treatment.
4. **A Python import of anything can hang** while OneDrive syncs the `.venv`.
   Give imports generous timeouts; prefer directory-existence checks over
   `import` in shell scripts.
5. Never commit: real EPWs, standards PDFs, `data/uploads/`, `data/runs/`,
   `data/mitigation/`, `logs/` (`.gitignore` already covers uploads/runs/
   mitigation — verify `logs/` is added too).

## Current state (verified this session — do NOT redo)

DONE and green:
- **Science fix (critical):** `packages/overheatlens-core/overheatlens/worker/runner.py`
  `harvest_hourly` no longer merges zones (full `LEVEL:ROOM` keys) and harvests
  only `(Hourly)` columns; duplicates raise. Regression tests in
  `packages/overheatlens-core/tests/test_harvest.py`; matrix rows VAL-XSIM-05/06.
- **Archetype provenance:** `data/archetypes/provenance.json` rebuilt for all 15
  IDFs (`scripts/build_archetype_provenance.py`); `scripts/audit_archetypes.py`
  ran the 15-model EnergyPlus 25.1.0 regression → 15/15 complete, 0 fatal/severe,
  TM59:2017 = 11 PASS / 4 FAIL (legitimate: 01BA, 17BG, 27BG, 52NP + TM59 Ex4 flat
  fail DSY1-High50). Report at `data/archetypes/audit_report.json`.
- **Backend** `apps/api/app/main.py`: persistent run archive (`data/runs/`,
  GET/DELETE `/api/runs[/{id}]`), `POST /api/batch`, `GET /api/models/detail`,
  `GET /api/mitigation/catalogue`, `GET /api/bundle` (reproducibility ZIP),
  research model `kind`/`era`/`research_status` in `/api/models`.
- **Frontend Neo-Brutalist rebuild:** `apps/web/src/nb-tokens.css`,
  `shell.css`, `charts.tsx`, `components.tsx`, 13 routes (`/runs`, `/scenarios`
  added; `/mitigation` real), all pages rebuilt, images in `apps/web/public/img/`
  (hero-lab.png + 4 empty-state images), ⌘K extended, footer
  `OverheatLens · Mohamed Hamdy Ali · MIT`.
- **Tests:** core **145 passed**, API **34 passed** (run 2026-09-04).
  `tsc -b` green; `vite build` green (after the zrender eviction fix).
- **Docs:** README, CHANGELOG (0.8.0.dev0), IMPLEMENTATION_STATUS, DESIGN.md v2.0,
  VALIDATION_MATRIX (VAL-XSIM-05/06), ARCHITECTURE_DECISIONS (ADR-0013..0015).
- **Launchers:** `Start/Close/Reset/Run Tests/Run Full Validation` exist for
  .command/.sh/.bat. NEW `Debug OverheatLens.{command,sh,bat}` created (port 8621,
  auto-reload, debug log `logs/overheatlens-debug.log`, startup self-check) but
  **not fully verified end-to-end** (see TODO-2).

## TODO LIST (in priority order)

### TODO-1 — Fix a bug I left in the Debug launchers (macOS/Linux)
**Problem:** `Debug OverheatLens.command` and `.sh` check for debug extras with
`if [ ! -d $SITE_PKGS/httpx ]` where `SITE_PKGS=".venv/lib/python3*/site-packages"`.
The glob can fail to match in a `[ -d ]` test, so it tries to
`pip install pytest httpx` — which hung (OneDrive) and is unnecessary anyway: the
debug server does not need pytest/httpx. **Fix:** remove the extras install block
entirely from `.command` and `.sh` (and the equivalent block in `.bat`), or make
the check robust (`ls -d .venv/lib/python*/site-packages/httpx >/dev/null 2>&1`)
and install quietly with `--no-cache-dir`. The venv already has all server deps.
**Files:** `Debug OverheatLens.command`, `Debug OverheatLens.sh`,
`Debug OverheatLens.bat`.
**Validate:** `bash -n` each; then TODO-2 end-to-end.

### TODO-2 — Verify the three debug launchers end-to-end (macOS primary)
Wait for OneDrive to be quiet (no heavy CPU in `OneDrive.app`; `df` stable).
Then:
1. `bash "Debug OverheatLens.command"` — expect: self-check prints core version,
   EnergyPlus 25.1.0, rule packs, weather dir OK, web build OK; server serves
   `http://127.0.0.1:8621`; `logs/overheatlens-debug.log` written.
2. `curl -s http://127.0.0.1:8621/api/version` → `{"core_version":"0.7.0.dev0",...}`;
   `curl -s -o /dev/null -w "%{http_code}" http://127.0.0.1:8621/` → `200`;
   `.../img/hero-lab.png` → `200`.
3. Touch a file under `apps/` and confirm auto-reload restarts (reloader logs in
   the log file); then `DEBUG_NORELOAD=1 bash "Debug OverheatLens.command"` variant
   boots without reload.
4. Run `bash "Close OverheatLens.command"` → confirms all OverheatLens processes
   closed (it pkills `uvicorn apps.api.app.main`, which matches port 8621 too).
5. Repeat for `.bat` on Windows if available (structure mirrors Start; the
   PowerShell `Tee-Object` log line must work).
**Fix anything broken** (e.g. the log `tee` swallowing uvicorn startup, the
self-check python string, the `open`/`xdg-open` calls). Add a one-line note in
`apps/web/src/pages/Info.tsx` Docs section if behaviour differs.

### TODO-3 — Run the web unit suite and make it pass (12 tests)
Copy `apps/web` to a local disk (keep `node_modules` reachable — copy or symlink
it, and also copy `apps/web/public`), then:
```
cd <local copy>/apps/web && npm run test   # vitest run
```
`apps/web/tests/components.test.tsx` has 12 tests (StatusPill, Figure,
BrandMark, AppShell nav incl. new /runs & /scenarios links, ResultVerdict,
MarginBar, StandardBadge incl. RESEARCH ONLY tag). Fix any real regressions (the
new components were added without a live run). If it still hangs even on local
disk (Node 24/26, vitest 4.1.11), record that as an environment limitation and
provide the `--pool=vmThreads`/`--pool=forks` evidence you tried.
**Also:** keep `vite.config.ts` test block sane (currently `pool: 'vmThreads'`).
`tsc -b` and `vite build` must stay green in place after your changes.

### TODO-4 — Full-suite verification + numbers for the final report
Run and record exact counts (note OneDrive can stall; retry on local disk if needed):
- Core: `PYTHONPATH=packages/overheatlens-core ./.venv/bin/python -m pytest packages/overheatlens-core/tests -q`
  → expect 145 passed (includes new `test_harvest.py`).
- API: `PYTHONPATH="packages/overheatlens-core:apps" ./.venv/bin/python -m pytest apps/api/tests -q`
  → expect 34 passed.
- Web: see TODO-3 (12 tests).
- Live pipeline smoke (needs local EnergyPlus + Leeds weather dir):
  `PYTHONPATH="packages/overheatlens-core:apps" ./.venv/bin/python -c` with
  `TestClient` hitting `POST /api/analyze` on `Leeds_DSY1_2020High50_.epw`
  `uk_tm59_2017` → expect 200, `result.overall` PASS/FAIL/INCOMPLETE, series keyed
  by `LEVEL:ROOM` (e.g. 01BA → 12 zones each 8760 values).
- Re-run `./.venv/bin/python scripts/audit_archetypes.py` (regenerates
  `data/archetypes/audit_report.json`) and confirm 15/15 complete + same verdicts.
Update `IMPLEMENTATION_STATUS.md` (last-updated line + test counts) and
`CHANGELOG.md` with the verified numbers.

### TODO-5 — Git hygiene (do NOT commit without asking)
- Add `logs/` to `.gitignore` (and confirm `data/runs/`, `data/mitigation/`,
  `data/uploads/` are listed).
- Decide with the user whether to commit `data/archetypes/audit_report.json`
  (it is safe: no external absolute paths, only filenames + hashes + results —
  recommend committing as regression evidence).
- Review `git status` and `git diff`; list every changed/untracked file in your
  final report. Stage and commit ONLY if the user explicitly asks; if not, leave
  the working tree staged-free and say so.
- Note: `Run Full Validation.{command,bat,sh}` are untracked (from a prior
  session) — verify they run (`./.venv/bin/python scripts/validate_science.py` and
  `scripts/validate_app.py` are referenced) and include them in the commit
  decision.

### TODO-6 — Optional stretch (only if the above is green and time allows)
These are genuinely optional; do not sacrifice TODO-1..5 for them.
- Standard diff viewer (TM59:2017 ↔ 2026): data-side is ready per
  `ARCHITECTURE_DECISIONS.md`; a small route + page could ship it.
- Simulation calendar drill-down (daily-max indoor temp, click → hourly zone
  profile) using the archived-run `series`.
- Weather × building matrix heatmap page that reads `/api/batch` results from
  `data/runs/` (functionally covered by Scenario & Batch table today).
- Sensitivity one-at-a-time UI (e.g. window-opening fraction) launching
  controlled `/api/batch` runs.
- 3D IDF geometry preview — explicitly out of scope unless requested; the Atlas
  dossier already lists geometry facts.

## Definition of done
1. TODO-1 fixed (no pip-extras block; launchers robust under sync stalls).
2. TODO-2 verified: debug server starts, serves `/`, `/img/*`, `/api/version`;
   auto-reload works; Close kills it; log file written.
3. TODO-3: web suite runs and passes (12/12) on local disk — or the hang is
   documented with the pool evidence you tried.
4. TODO-4: core 145 + API 34 green re-confirmed; live analyze smoke green;
   archetype regression re-confirmed; docs updated with final numbers.
5. TODO-5: `.gitignore` covers `logs/`; diff reviewed; commit only if asked.
6. Final report (short): what you changed (files), test counts (passed/failed/
   skipped), environment issues encountered, and anything left unverified.

## Useful file map
- Science: `packages/overheatlens-core/overheatlens/{worker/runner.py, standards/engine.py, epw/, idf/, comfort/}`
- API: `apps/api/app/main.py`, `apps/api/app/report.py`, `apps/api/tests/test_api.py`
- Web: `apps/web/src/{App.tsx, AppShell.tsx, nb-tokens.css, shell.css, charts.tsx, components.tsx, api.ts, CommandPalette.tsx, ThermalRibbon.tsx, ExportBar.tsx}`, `apps/web/src/pages/*`, `apps/web/tests/components.test.tsx`, `apps/web/vite.config.ts`
- Launchers: `Start/Close/Reset/Run Tests/Run Full Validation/Debug OverheatLens.{command,sh,bat}`
- Data/scripts: `data/archetypes/{idf/, provenance.json, audit_report.json, PROVENANCE.md}`, `scripts/{audit_archetypes.py, build_archetype_provenance.py, build_mitigation_catalogue.py, validate_science.py, validate_app.py}`
- Docs: `README.md, CHANGELOG.md, IMPLEMENTATION_STATUS.md, DESIGN.md, VALIDATION_MATRIX.md, ARCHITECTURE_DECISIONS.md, PRODUCT.md, DISCLAIMER.md`
- Governance: `LICENSE` (MIT, © 2026 Mohamed Hamdy Ali — attribution spelling is **Hamdy**, never Hamdi), `CITATION.cff`, `SOURCE_REGISTER.md`

**Guardrails:** never duplicate scientific calculations in JS; never silently
alter model physics; never present research-only results as compliance; never
fake success (INCOMPLETE is a valid verdict); respect the licence footer
`OverheatLens · Mohamed Hamdy Ali · MIT`; keep everything local-first.

==== END PROMPT ====

## How to hand this off

1. Copy everything between `==== BEGIN PROMPT` and `==== END PROMPT` above.
2. Paste it to the other AI worker in a new session, pointing it at the repo
   path (or a local-disk copy you made).
3. Tell it to **start with TODO-1** and report back after each TODO, and to ask
   before any `git commit`.

The file `DELEGATION_HANDOFF.md` (this document) is saved in the repo root so
it travels with the project.