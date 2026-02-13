@echo off
REM Simple server starter - most reliable method

cd /d "%~dp0"

echo Starting Sonora API Server...
echo.
echo This window must stay open!
echo.
echo Server: http://127.0.0.1:8000
echo Health:  http://127.0.0.1:8000/health
echo.

REM Try Python script first (most reliable)
py run_server_direct.py
if errorlevel 1 (
    echo.
    echo Python script failed, trying uvicorn directly...
    echo.
    py -m uvicorn api.server:app --host 127.0.0.1 --port 8000
)

pause









