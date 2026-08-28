# Contributing to OverheatLens

Thanks for your interest. OverheatLens is research software with scientific-accuracy gates.

## Ground rules

1. **No threshold without a source.** Any numeric criterion added to a rule pack must have an
   entry in `SOURCE_REGISTER.md` with its verification status, in the same commit.
2. **Never weaken a failing test** to make it pass. Investigate the cause; document the resolution.
3. **Authoritative calculations live only in `packages/overheatlens-core`.** No formulas in the
   frontend; web-side previews must be labelled and parity-tested against core.
4. **Real weather files and licensed standards PDFs are never committed** (`.gitignore` enforces).
5. Every phase completion updates `IMPLEMENTATION_STATUS.md` and `VALIDATION_MATRIX.md`.

## Local development

Double-click `Run Tests.command` (macOS) / `Run Tests.bat` (Windows), or:

```bash
python3.12 -m venv .venv && ./.venv/bin/pip install numpy PyYAML pythermalcomfort pytest pytest-cov hypothesis
./.venv/bin/python -m pytest packages/overheatlens-core/tests -q
```

## Pull requests

- One logical change per PR; tests must pass locally before opening.
- New scientific behaviour requires new validation-matrix rows.
- Commits: short imperative subject; body explains the scientific decision if any.
