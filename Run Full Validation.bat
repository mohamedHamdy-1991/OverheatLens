@echo off
rem Full application validation (Windows) - see scripts\validate_app.py
cd /d "%~dp0"
if exist ".venv\Scripts\python.exe" (set "PY=.venv\Scripts\python.exe") else (
  echo Setting up OverheatLens first - run Start OverheatLens once.
  pause & exit /b 1
)
".venv\Scripts\python.exe" -c "import fastapi" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install --quiet fastapi "uvicorn[standard]" pypdf cryptography
set "PYTHONPATH=%~dp0packages\overheatlens-core;%~dp0apps"
echo Running full application validation - this can take several minutes...
"%PY%" scripts\validate_app.py
echo.
echo Report: docs\validation\FULL_APP_VALIDATION_REPORT.md
pause
