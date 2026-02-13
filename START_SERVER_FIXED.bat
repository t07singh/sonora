@echo off
REM Fixed startup script for Sonora API Server
REM This script properly handles the import path

echo ========================================
echo Starting Sonora API Server (Fixed)
echo ========================================
echo.

REM Change to sonora directory
cd /d "%~dp0sonora"
if not exist "api\server.py" (
    echo ERROR: Cannot find api\server.py
    echo Current directory: %CD%
    pause
    exit /b 1
)

echo Current directory: %CD%
echo.

REM Check Python
python --version >nul 2>&1
if errorlevel 1 (
    echo ERROR: Python not found
    pause
    exit /b 1
)

echo Starting server on http://127.0.0.1:8000
echo Health check: http://127.0.0.1:8000/health
echo.
echo Press Ctrl+C to stop the server
echo.

REM Start server - use api.server:app when running from sonora directory
python -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload

pause









