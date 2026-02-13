@echo off
REM ============================================================
REM Check and Start Sonora Server
REM ============================================================

cd /d "%~dp0"

echo.
echo ============================================================
echo   SONORA SERVER - CHECK AND START
echo ============================================================
echo.

REM Step 1: Check if port is in use
echo [1/4] Checking if port 8000 is available...
netstat -ano | findstr :8000 >nul
if %errorlevel% == 0 (
    echo ⚠️  Port 8000 is in use!
    echo.
    echo Processes using port 8000:
    netstat -ano | findstr :8000
    echo.
    set /p kill="Kill these processes? (Y/N): "
    if /i "%kill%"=="Y" (
        for /f "tokens=5" %%a in ('netstat -ano ^| findstr :8000') do (
            echo Killing process %%a...
            taskkill /PID %%a /F >nul 2>&1
        )
        timeout /t 2 >nul
        echo ✅ Port cleared
    ) else (
        echo Using different port 8001...
        set PORT=8001
    )
) else (
    echo ✅ Port 8000 is available
    set PORT=8000
)

echo.
echo [2/4] Testing Python and imports...
py -c "from api.server import app; print('✅ Imports OK')" 2>nul
if errorlevel 1 (
    echo ❌ Import test failed!
    echo.
    echo Running full diagnostic...
    py test_server_startup.py --diagnostic-only
    echo.
    pause
    exit /b 1
)
echo ✅ Python and imports working

echo.
echo [3/4] Starting server on port %PORT%...
echo.
echo ============================================================
echo   SERVER STARTING - KEEP THIS WINDOW OPEN!
echo ============================================================
echo.
echo Server URL: http://127.0.0.1:%PORT%
echo Health:     http://127.0.0.1:%PORT%/health
echo.
echo ============================================================
echo.

REM Start server
if "%PORT%"=="8001" (
    py -m uvicorn api.server:app --host 127.0.0.1 --port 8001 --reload
) else (
    py -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload
)

echo.
echo Server stopped.
pause









