@echo off
rem Double-click to STOP all OverheatLens services (Windows).
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*overheatlens.hub*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
powershell -NoProfile -Command "Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*apps.api.app.main*'} | ForEach-Object { Stop-Process -Id $_.ProcessId -Force }" >nul 2>&1
timeout /t 1 /nobreak >nul
powershell -NoProfile -Command "$left = Get-CimInstance Win32_Process | Where-Object {$_.CommandLine -like '*apps.api.app.main*' -or $_.CommandLine -like '*overheatlens.hub*'}; if ($left) { Write-Host 'Some OverheatLens processes are still running - run this again.' } else { Write-Host 'All OverheatLens services are closed.' }"
echo You can now close this window and any OverheatLens browser tabs.
pause
