# OverheatLens

**See the heat. Trace the evidence. Test the response.**

OverheatLens is an open, version-aware research-software platform for building-overheating
assessment: weather-file intelligence, model readiness, EnergyPlus simulation, versioned
overheating standards (TM59:2017, TM59:2026, Approved Document O dynamic route, TM52),
thermal-comfort analytics, mitigation testing and reproducible evidence export.

> **Status: early development (Phase 0–2).** The scientific core, rule-pack system and
> EPW engine are under active construction. Nothing here is yet a compliance tool.
> See [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md).

---

## Quick start (no installation steps — double-click)

| What you want | macOS | Windows |
|---|---|---|
| Start OverheatLens | `Start OverheatLens.command` | `Start OverheatLens.bat` |
| Run the full local test suite | `Run Tests.command` | `Run Tests.bat` |
| Stop everything | `Close OverheatLens.command` | `Close OverheatLens.bat` |

The first run creates a private Python environment inside the project folder
(`.venv`) and installs its own dependencies. Later runs start instantly.
You never need to install anything by hand.

## For developers and researchers

```bash
# scientific core CLI (after one start via the launcher above)
./.venv/bin/python -m overheatlens version
./.venv/bin/python -m overheatlens rule-packs
./.venv/bin/python -m overheatlens check-epw fixtures/epw/synthetic/good_file.epw

# tests
./.venv/bin/python -m pytest packages/overheatlens-core/tests -q
```

## Repository layout

```text
packages/overheatlens-core/   scientific Python package (authoritative calculations)
apps/web                      React + TypeScript interface (Phase 8+)
apps/api                      FastAPI service (Phase 7+)
apps/worker                   EnergyPlus runner (Phase 6+)
packages/../rules/            versioned standards rule packs (YAML + JSON Schema)
fixtures/                     synthetic test EPWs/IDFs (real weather never committed)
docs/specs/                   governing build specifications (single source of truth)
docs/standards/               standards verification notes (sources, status)
```

## Governance documents

- [IMPLEMENTATION_STATUS.md](IMPLEMENTATION_STATUS.md) — what is built, tested, verified
- [SOURCE_REGISTER.md](SOURCE_REGISTER.md) — every standards source and its verification status
- [ARCHITECTURE_DECISIONS.md](ARCHITECTURE_DECISIONS.md) — decision records
- [VALIDATION_MATRIX.md](VALIDATION_MATRIX.md) — live validation evidence

## Important notice

OverheatLens is open research and decision-support software. It is **not** a certified
compliance certificate. Formal submissions must use the applicable current requirements
and be reviewed by a suitably qualified professional. See [DISCLAIMER.md](DISCLAIMER.md).

## Licence

MIT — see [LICENSE](LICENSE).
