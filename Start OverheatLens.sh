#!/bin/bash
# Run from a terminal to start OverheatLens (Linux).
# First run creates a private Python environment and installs its own dependencies;
# later runs start in seconds. Serves the app at http://127.0.0.1:8620 and opens it.
cd "$(dirname "$0")" || exit 1

PORT=8620

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  echo "Setting up OverheatLens (first run only — a minute or two)…"
  PY_SRC=""
  for cand in python3.12 python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then PY_SRC="$cand"; break; fi
  done
  if [ -z "$PY_SRC" ]; then
    echo "Python 3 is required — install python3 and start again."
    exit 1
  fi
  "$PY_SRC" -m venv .venv || { echo "Could not create a Python environment."; exit 1; }
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet numpy PyYAML pythermalcomfort fastapi "uvicorn[standard]" pypdf cryptography
  PY=".venv/bin/python"
fi

# API deps must be present even if the venv predates the web app.
./.venv/bin/python -c "import fastapi, uvicorn" 2>/dev/null \
  || ./.venv/bin/pip install --quiet fastapi "uvicorn[standard]"

# Build the web app if needed (first run, or sources newer than the build).
if [ ! -f apps/web/dist/index.html ]; then
  if command -v npm >/dev/null 2>&1; then
    echo "Building the interface (first run only — one to two minutes)…"
    (cd apps/web && npm install --silent && npm run build --silent) \
      || { echo "The interface build failed — is Node.js installed?"; exit 1; }
  else
    echo "Node.js not found — the interface needs it once to build."
    echo "Install Node from https://nodejs.org and start again."
    exit 1
  fi
fi

export PYTHONPATH="packages/overheatlens-core:$PYTHONPATH"
echo ""
echo "  OverheatLens is running →  http://127.0.0.1:${PORT}"
echo "  Close it with “Close OverheatLens” or Ctrl+C here."
echo ""
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:${PORT}" >/dev/null 2>&1
else
  echo "  Open http://127.0.0.1:${PORT} in your browser."
fi
exec "$PY" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port "$PORT"
