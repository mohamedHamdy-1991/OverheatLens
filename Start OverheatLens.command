#!/bin/bash
# Double-click to start OverheatLens (macOS).
# First run creates a private Python environment; later runs start instantly.
cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  echo "Setting up OverheatLens (first run only — a minute or two)…"
  # Prefer a modern Homebrew Python if present, else fall back to system python3.
  for cand in /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.12 /usr/local/bin/python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then PY_SRC="$cand"; break; fi
  done
  "$PY_SRC" -m venv .venv || { echo "Could not create a Python environment."; exit 1; }
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet numpy PyYAML pythermalcomfort
  PY=".venv/bin/python"
fi

export PYTHONPATH="packages/overheatlens-core:$PYTHONPATH"
exec "$PY" -m overheatlens.hub
