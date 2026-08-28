@echo off
rem Double-click to run the full OverheatLens local test suite (Windows).
cd /d "%~dp0"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  echo Setting up OverheatLens (first run only - a minute or two)...
  python -m venv .venv || (echo Python 3 is required. Install it from python.org and try again. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet numpy PyYAML pythermalcomfort pytest pytest-cov hypothesis
  set "PY=.venv\Scripts\python.exe"
)

".venv\Scripts\python.exe" -c "import hypothesis" >nul 2>&1
if errorlevel 1 ".venv\Scripts\python.exe" -m pip install --quiet hypothesis pytest pytest-cov

set "PYTHONPATH=%~dp0packages\overheatlens-core;%PYTHONPATH%"
echo Running the OverheatLens test suite...
"%PY%" -m pytest packages\overheatlens-core\tests -q --color=yes
echo.
echo Done.
pause
