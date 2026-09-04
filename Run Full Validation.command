#!/bin/bash
# Double-click to run the FULL application validation (macOS):
# every layer is tested and a dated report is written to
# docs/validation/FULL_APP_VALIDATION_REPORT.md
cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  echo "Setting up OverheatLens first (run Start OverheatLens once)."
  exit 1
fi

./.venv/bin/python -c "import fastapi" 2>/dev/null || ./.venv/bin/pip install --quiet fastapi "uvicorn[standard]" pypdf cryptography

export PYTHONPATH="packages/overheatlens-core:apps"
echo "Running full application validation — this can take several minutes…"
"$PY" scripts/validate_app.py
echo ""
echo "Report: docs/validation/FULL_APP_VALIDATION_REPORT.md"
echo "Press any key to close."
read -n 1 -s
