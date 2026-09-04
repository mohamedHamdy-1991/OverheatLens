@echo off
rem Double-click to start OverheatLens in DEBUG mode (Windows).
rem Same app as Start, but on port 8621 with auto-reload, debug logging,
rem a startup self-check, and a log file at logs\overheatlens-debug.log.
rem Close it with "Close OverheatLens" (kills debug too) or Ctrl+C here.
cd /d "%~dp0"

set "PORT=8621"
set "LOG=logs\overheatlens-debug.log"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  echo Setting up OverheatLens (first run only - a minute or two)...
  python -m venv .venv || (echo Could not create a Python environment. Install Python 3 from python.org and try again. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet numpy PyYAML pythermalcomfort fastapi "uvicorn[standard]" pypdf cryptography pytest httpx
  set "PY=.venv\Scripts\python.exe"
)

rem Web build must exist (debug does not rebuild it - use Start once first).
if not exist "apps\web\dist\index.html" (
  echo The interface is not built yet - run "Start OverheatLens" once first,
  echo then use this debug launcher.
  pause
  exit /b 1
)

if not exist "logs" mkdir "logs"
set "PYTHONPATH=packages\overheatlens-core;%PYTHONPATH%"

echo --- OverheatLens debug self-check ---
".venv\Scripts\python.exe" -u -c "from overheatlens import CORE_VERSION; print('core:', CORE_VERSION)" 2>&1
".venv\Scripts\python.exe" -u -c "from overheatlens.worker import find_energyplus; b=find_energyplus(); print('energyplus:', b[0]['version'], b[0]['binary']) if b else print('energyplus: NONE FOUND')" 2>&1
".venv\Scripts\python.exe" -u -c "from overheatlens.schemas import available_pack_ids; print('rule packs:', ', '.join(sorted(available_pack_ids())))" 2>&1
echo.
echo   DEBUG mode at http://127.0.0.1:%PORT%  (auto-reload on, debug log)
echo   Log file:  %LOG%
echo   Close it with "Close OverheatLens" or Ctrl+C here.
echo   Set DEBUG_NORELOAD=1 to run without auto-reload.
echo.
echo   NOTE: if the server exits immediately with file-read timeouts, OneDrive is
echo   still syncing this folder - wait a minute and start again, or right-click
echo   the OverheatLens folder in Explorer - "Always keep on this device".
echo.
start "" http://127.0.0.1:%PORT%
if defined DEBUG_NORELOAD (
  powershell -NoProfile -Command "& '.venv\Scripts\python.exe' -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port %PORT% --log-level debug 2>&1 | Tee-Object -FilePath '%LOG%' -Append"
) else (
  powershell -NoProfile -Command "& '.venv\Scripts\python.exe' -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port %PORT% --reload --reload-dir apps --reload-dir packages --log-level debug 2>&1 | Tee-Object -FilePath '%LOG%' -Append"
)
pause
