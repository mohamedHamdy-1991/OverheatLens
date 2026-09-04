#!/bin/bash
# Run from a terminal to start OverheatLens in DEBUG mode (Linux).
# Same app as Start, but on port 8621 with auto-reload, debug logging,
# a startup self-check, and a log file at logs/overheatlens-debug.log.
# Close it with "Close OverheatLens" (kills debug too) or Ctrl+C here.
cd "$(dirname "$0")" || exit 1

PORT=8621
LOG="logs/overheatlens-debug.log"

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
  ./.venv/bin/pip install --quiet numpy PyYAML pythermalcomfort fastapi "uvicorn[standard]" pypdf cryptography pytest httpx
  PY=".venv/bin/python"
fi

# Web build must exist (debug does not rebuild it — use Start once first).
if [ ! -f apps/web/dist/index.html ]; then
  echo "The interface is not built yet — run “Start OverheatLens” (Start OverheatLens.sh) once first,"
  echo "then use this debug launcher."
  exit 1
fi

mkdir -p logs
export PYTHONPATH="packages/overheatlens-core:$PYTHONPATH"

echo "--- OverheatLens debug self-check ---"
set -o pipefail
CHECK_OK=0
for attempt in 1 2 3; do
  if "$PY" -u -c "
from overheatlens import CORE_VERSION
print('core:', CORE_VERSION)
try:
    from overheatlens.worker import find_energyplus
    bins = find_energyplus()
    print('energyplus:', bins[0]['version'], '(' + bins[0]['binary'] + ')' if bins else 'NONE FOUND')
except Exception as e:
    print('energyplus: PROBE FAILED:', e)
try:
    from overheatlens.schemas import available_pack_ids
    print('rule packs:', ', '.join(sorted(available_pack_ids())))
except Exception as e:
    print('rule packs: FAILED:', e)
import os
from pathlib import Path
wd = Path(os.environ.get('OVERHEATLENS_WEATHER_DIR', '.'))
print('weather dir:', 'OK' if wd.is_dir() else 'MISSING', '-', wd)
if wd.is_dir():
    print('weather files:', len(list(wd.glob('*.epw'))))
print('web build: OK' if Path('apps/web/dist/index.html').is_file() else 'web build: MISSING')
" 2>&1 | tee "$LOG"; then
    CHECK_OK=1
    break
  fi
  echo "Self-check hit a file-read stall (cloud sync still running?) — retrying ($attempt/3)…" | tee -a "$LOG"
  sleep 15
done
[ "$CHECK_OK" = "1" ] || echo "Self-check could not complete — starting the server anyway; see ${LOG}." | tee -a "$LOG"

echo ""
echo "  DEBUG mode →  http://127.0.0.1:${PORT}  (auto-reload on, debug log)"
echo "  Log file:  ${LOG}"
echo "  Close it with “Close OverheatLens” or Ctrl+C here."
echo "  Set DEBUG_NORELOAD=1 to run without auto-reload."
echo ""
echo "  NOTE: if the server exits immediately with file-read timeouts, the cloud"
echo "  drive is still syncing this folder — wait a minute and start again."
echo ""
if command -v xdg-open >/dev/null 2>&1; then
  xdg-open "http://127.0.0.1:${PORT}" >/dev/null 2>&1
else
  echo "  Open http://127.0.0.1:${PORT} in your browser."
fi
if [ -n "$DEBUG_NORELOAD" ]; then
  "$PY" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port "$PORT" \
    --log-level debug 2>&1 | tee -a "$LOG"
  exit 0
fi
"$PY" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port "$PORT" \
  --reload --reload-dir apps --reload-dir packages \
  --log-level debug 2>&1 | tee -a "$LOG"
