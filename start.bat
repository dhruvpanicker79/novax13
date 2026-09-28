@echo off
REM Serve the built KSHETRA app. No Node, no WSL, no network needed
REM beyond the satellite basemap tiles.
cd /d "%~dp0dist"
echo.
echo   KSHETRA  --  http://127.0.0.1:8080
echo   Leave this window open. Ctrl+C to stop.
echo.
start "" http://127.0.0.1:8080
"%~dp0.venv\Scripts\python.exe" -m http.server 8080 --bind 127.0.0.1
