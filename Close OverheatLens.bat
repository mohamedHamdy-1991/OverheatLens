@echo off
rem Double-click to STOP all OverheatLens services (Windows).
taskkill /F /FI "WINDOWTITLE eq OverheatLens*" >nul 2>&1
wmic process where "CommandLine like '%%overheatlens%%'" call terminate >nul 2>&1
echo OverheatLens services stopped (if any were running).
echo You can now close this window and any OverheatLens browser tabs.
pause
