#!/bin/bash
# Double-click to run the full OverheatLens local test suite (macOS).
cd "$(dirname "$0")" || exit 1

if [ -x ".venv/bin/python" ]; then
  PY=".venv/bin/python"
else
  echo "Setting up OverheatLens (first run only — a minute or two)…"
  for cand in /opt/homebrew/bin/python3.12 /opt/homebrew/bin/python3.11 /usr/local/bin/python3.12 /usr/local/bin/python3.11 python3; do
    if command -v "$cand" >/dev/null 2>&1; then PY_SRC="$cand"; break; fi
  done
  "$PY_SRC" -m venv .venv || { echo "Could not create a Python environment."; exit 1; }
  ./.venv/bin/pip install --quiet --upgrade pip
  ./.venv/bin/pip install --quiet numpy PyYAML pythermalcomfort pytest pytest-cov hypothesis
  PY=".venv/bin/python"
fi

# Make sure test dependencies are present even if .venv already existed.
./.venv/bin/python -c "import hypothesis" 2>/dev/null || ./.venv/bin/pip install --quiet hypothesis pytest pytest-cov

export PYTHONPATH="packages/overheatlens-core:$PYTHONPATH"
echo "Running the OverheatLens test suite…"
"$PY" -m pytest packages/overheatlens-core/tests -q --color=yes
echo ""
echo "Done. Press any key to close this window."
read -n 1 -s
