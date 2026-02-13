@echo off
REM Quick server starter - shows output and keeps window open

echo ========================================
echo Starting Sonora API Server
echo ========================================
echo.

cd /d "%~dp0"

echo Current directory: %CD%
echo.
echo Starting server on http://127.0.0.1:8000
echo Health check: http://127.0.0.1:8000/health
echo API docs: http://127.0.0.1:8000/docs
echo.
echo Press Ctrl+C to stop the server
echo.

py -m uvicorn api.server:app --host 127.0.0.1 --port 8000

pause









