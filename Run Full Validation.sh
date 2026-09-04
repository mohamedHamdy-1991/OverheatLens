#!/bin/bash
# Full application validation (Linux) — see scripts/validate_app.py
cd "$(dirname "$0")" || exit 1
if [ -x ".venv/bin/python" ]; then PY=".venv/bin/python"; else
  echo "Setting up OverheatLens first (run Start OverheatLens once)."; exit 1
fi
./.venv/bin/python -c "import fastapi" 2>/dev/null || ./.venv/bin/pip install --quiet fastapi "uvicorn[standard]" pypdf cryptography
export PYTHONPATH="packages/overheatlens-core:apps"
echo "Running full application validation — this can take several minutes…"
"$PY" scripts/validate_app.py
echo ""
echo "Report: docs/validation/FULL_APP_VALIDATION_REPORT.md"
