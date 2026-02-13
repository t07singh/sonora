@echo off
REM ============================================================
REM Sonora Server Startup - Debug Mode
REM This shows ALL output and errors
REM ============================================================

echo.
echo ============================================================
echo   SONORA API SERVER - DEBUG MODE
echo ============================================================
echo.
echo Current directory: %CD%
echo.
echo This will start the server and show ALL output.
echo If there are errors, you'll see them here.
echo.
echo ============================================================
echo.

REM Test import first
echo [1/3] Testing imports...
py -c "from api.server import app; print('✅ Import successful')" 2>&1
if errorlevel 1 (
    echo.
    echo ❌ IMPORT FAILED - Check errors above
    echo.
    pause
    exit /b 1
)

echo.
echo [2/3] Starting server...
echo.
echo Server will be at: http://127.0.0.1:8000
echo Health check: http://127.0.0.1:8000/health
echo.
echo ============================================================
echo   SERVER OUTPUT (Keep this window open!)
echo ============================================================
echo.

REM Start server - this will show all output
py -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload

echo.
echo ============================================================
echo   Server stopped
echo ============================================================
pause









