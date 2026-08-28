@echo off
rem Double-click to start OverheatLens (Windows).
rem First run creates a private Python environment; later runs start instantly.
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  echo Setting up OverheatLens (first run only - a minute or two)...
  python -m venv .venv || (echo Python 3 is required. Install it from python.org and try again. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet numpy PyYAML pythermalcomfort
  set "PY=.venv\Scripts\python.exe"
)

set "PYTHONPATH=%~dp0packages\overheatlens-core;%PYTHONPATH%"
"%PY%" -m overheatlens.hub
pause
