# OverheatLens

**See the heat. Trace the evidence. Test the response.**

OverheatLens is an open, version-aware research-software platform for domestic
building-overheating assessment: weather-file intelligence, model readiness,
EnergyPlus simulation, versioned overheating standards (TM59:2017, TM59:2026,
Approved Document O dynamic route, TM52), thermal-comfort analytics, mitigation
testing and reproducible evidence export.

> **Status: research software under active development.** The scientific core,
> rule-pack system, EPW engine, EnergyPlus worker and web laboratory are built
> and tested; nothing here is a certified compliance tool.
> See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) and the in-app
> Validation page (which reads [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) live).

---

## Quick start (no installation steps — double-click)

| What you want | macOS | Windows | Linux |
|---|---|---|---|
| Start OverheatLens | `Start OverheatLens.command` | `Start OverheatLens.bat` | `Start OverheatLens.sh` |
| Run the full local test suite | `Run Tests.command` | `Run Tests.bat` | — |
| Run full validation | `Run Full Validation.command` | `Run Full Validation.bat` | — |
| Stop everything | `Close OverheatLens.command` | `Close OverheatLens.bat` | `Close OverheatLens.sh` |
| Reset to first run | `Reset OverheatLens.command` | `Reset OverheatLens.bat` | `Reset OverheatLens.sh` |

The first run creates a private Python environment inside the project folder
(`.venv`) and installs its own dependencies. Later runs start instantly.
You never need to install anything by hand.
On Linux, run the `.sh` scripts from a terminal (for example
`bash "Start OverheatLens.sh"`).
The reset script stops the server and removes the built interface — your files
and weather data are not touched; the next Start rebuilds everything.

The app opens at `http://127.0.0.1:8620`: the **laboratory desktop** with
Analyze, Weather Lab, Archetype Atlas, Comfort Lab, Compare, Mitigation Lab,
Run Archive, Scenario & Batch, Validation, Methods, Docs and About.

## The workflow

```
1. CHOOSE BUILDING        research archetype · generic template · upload IDF
2. CHOOSE WEATHER          local library EPW · upload EPW (QC on arrival)
3. CHOOSE ANALYSIS         TM59:2017 · TM59:2026 · Part O dynamic · TM52 · comfort
4. CHECK READINESS         model + weather + standard, every finding explained
5. RUN ENERGYPLUS          official local binary (25.1.0 working pin), real stages
6. VALIDATE RUN            err interpreter, output completeness, INCOMPLETE honesty
7. ANALYSE RESULTS         verdict + threshold margins + zone × time evidence
8. EXPORT EVIDENCE         report HTML · results JSON · reproducibility ZIP bundle
```

Every simulation is an **experiment** (building + weather + method + engine) with
a run ID linking outputs, charts, criteria, hashes and exports. Every number
traces to its source: SIMULATED, DERIVED, ASSUMED, USER INPUT or RESEARCH DATA.

## For developers and researchers

```bash
# scientific core CLI (after one start via the launcher above)
./.venv/bin/python -m overheatlens version
./.venv/bin/python -m overheatlens rule-packs
./.venv/bin/python -m overheatlens check-epw fixtures/epw/synthetic/good_file.epw

# tests (core is authoritative; API + web cover the service and interface)
PYTHONPATH=packages/overheatlens-core ./.venv/bin/python -m pytest packages/overheatlens-core/tests -q
PYTHONPATH="packages/overheatlens-core:apps" ./.venv/bin/python -m pytest apps/api/tests -q
# web: typecheck + build + unit tests (see apps/web/package.json)
./apps/web/node_modules/.bin/tsc -b --project apps/web
./apps/web/node_modules/.bin/vite build --config apps/web/vite.config.ts

# archetype regression: all 15 bundled IDFs × reference EPW (needs local E+ + weather)
./.venv/bin/python scripts/audit_archetypes.py
./.venv/bin/python scripts/build_archetype_provenance.py     # refresh data/archetypes/provenance.json
./.venv/bin/python scripts/build_mitigation_catalogue.py     # rebuild data/mitigation/summary.json (local only)
```

## Repository layout

```text
packages/overheatlens-core/   scientific Python package (authoritative calculations)
apps/web                      React + TypeScript laboratory (Neo-Brutalist design system)
apps/api                      FastAPI service (analyze, archive, batch, bundles, catalogue)
apps/worker                   EnergyPlus runner placeholder (live runner is core worker/)
packages/../rules/            versioned standards rule packs (YAML + JSON Schema)
data/archetypes/idf/          15 audited research/model IDFs + provenance.json
data/mitigation/              Harehills catalogue (generated locally, never committed)
data/runs/                    persistent run archive (local only, never committed)
data/uploads/                 your IDF/EPW uploads (local only, never committed)
fixtures/                     synthetic test EPWs/IDFs (real weather never committed)
scripts/                      audit/provenance/catalogue/validation utilities
docs/specs/                   governing build specifications (single source of truth)
docs/standards/               standards verification notes (sources, status)
```

## Governance documents

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) — what is built, tested, verified
- [SOURCE_REGISTER.md](SOURCE_REGISTER.md) — every standards source and its verification status
- [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) — decision records
- [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) — live validation evidence
- [DESIGN.md](DESIGN.md) — visual world and tokens (Neo-Brutalist system)
- [PRODUCT.md](PRODUCT.md) — product definition and non-negotiables

## Important notice

OverheatLens is open research and decision-support software. It is **not** a certified
compliance certificate. Formal submissions must use the applicable current requirements
and be reviewed by a suitably qualified professional. See [DISCLAIMER.md](DISCLAIMER.md).

## Licence

MIT — see [LICENSE](LICENSE). OverheatLens · Mohamed Hamdy Ali.
