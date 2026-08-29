@echo off
rem Double-click to RESET OverheatLens (Windows): stops the server and removes
rem the built interface so the next start rebuilds it (first run again).
rem Your files and weather data are not touched.
cd /d "%~dp0"

echo This removes the built interface and stops the server. Your files and weather data are not touched.
echo.

powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*apps.api.app.main*' -or $_.CommandLine -like '*overheatlens.hub*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
timeout /t 1 /nobreak >nul

if exist "apps\web\dist" rmdir /s /q "apps\web\dist"

echo   Stopped any running OverheatLens server.
echo   Removed the built interface (apps\web\dist).
echo   Any run state lives only in the running server - it resets when the server restarts.
echo.
echo   The next time you start OverheatLens it will rebuild everything
echo   (first run again - a minute or two).
pause
