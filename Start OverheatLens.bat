@echo off
rem Double-click to start OverheatLens (Windows).
rem First run creates a private Python environment and installs its own dependencies;
rem later runs start in seconds. Serves the app at http://127.0.0.1:8620 and opens it.
cd /d "%~dp0"

set "PORT=8620"

if exist ".venv\Scripts\python.exe" (
  set "PY=.venv\Scripts\python.exe"
) else (
  echo Setting up OverheatLens (first run only - a minute or two)...
  python -m venv .venv || (echo Could not create a Python environment. Install Python 3 from python.org and try again. & pause & exit /b 1)
  ".venv\Scripts\python.exe" -m pip install --quiet --upgrade pip
  ".venv\Scripts\python.exe" -m pip install --quiet numpy PyYAML pythermalcomfort fastapi "uvicorn[standard]" pypdf cryptography
  set "PY=.venv\Scripts\python.exe"
)

rem API deps must be present even if the venv predates the web app.
".venv\Scripts\python.exe" -c "import fastapi, uvicorn" 2>nul || ".venv\Scripts\python.exe" -m pip install --quiet fastapi "uvicorn[standard]"

rem Build the web app if needed (first run, or sources newer than the build).
if not exist "apps\web\dist\index.html" (
  where npm >nul 2>&1
  if errorlevel 1 (
    echo Node.js not found - the interface needs it once to build.
    echo Install Node from https://nodejs.org and start again.
    pause
    exit /b 1
  )
  echo Building the interface (first run only - one to two minutes)...
  pushd apps\web
  call npm install --silent
  call npm run build --silent
  popd
  if not exist "apps\web\dist\index.html" (
    echo The interface build failed - is Node.js installed?
    pause
    exit /b 1
  )
)

set "PYTHONPATH=packages\overheatlens-core;%PYTHONPATH%"
echo.
echo   OverheatLens is running at http://127.0.0.1:%PORT%
echo   Close it with "Close OverheatLens" or Ctrl+C here.
echo.
start "" http://127.0.0.1:%PORT%
"%PY%" -m uvicorn apps.api.app.main:app --host 127.0.0.1 --port %PORT%
pause
