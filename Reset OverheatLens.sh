#!/bin/bash
# Run from a terminal to RESET OverheatLens (Linux): stops the server and
# removes the built interface so the next start rebuilds it (first run again).
# Your files and weather data are not touched.
cd "$(dirname "$0")" || exit 1

echo "This removes the built interface and stops the server. Your files and weather data are not touched."
echo ""

pkill -f "overheatlens.hub" 2>/dev/null
pkill -f "uvicorn apps.api.app.main" 2>/dev/null
sleep 1

rm -rf apps/web/dist

echo "  Stopped any running OverheatLens server."
echo "  Removed the built interface (apps/web/dist)."
echo "  Any run state lives only in the running server — it resets when the server restarts."
echo ""
echo "  The next time you start OverheatLens it will rebuild everything"
echo "  (first run again — a minute or two)."
sleep 2
