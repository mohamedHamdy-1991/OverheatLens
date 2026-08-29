#!/bin/bash
# Run from a terminal to STOP all OverheatLens services (Linux).
pkill -f "overheatlens.hub" 2>/dev/null
pkill -f "uvicorn apps.api.app.main" 2>/dev/null
sleep 1
if pgrep -f "overheatlens" >/dev/null 2>&1; then
  echo "Some OverheatLens processes are still running — run this again."
else
  echo "All OverheatLens services are closed."
  echo "You can now close this window and any OverheatLens browser tabs."
fi
sleep 2
