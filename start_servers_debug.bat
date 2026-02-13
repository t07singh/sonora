@echo off
echo ========================================
echo   SONORA SERVER STARTUP (DEBUG MODE)
echo ========================================
echo.

cd /d "%~dp0"

echo Step 1: Testing Python...
py --version
if errorlevel 1 (
    echo ERROR: Python not found!
    pause
    exit /b 1
)
echo.

echo Step 2: Starting API Server...
start "Sonora API (Port 8000)" cmd /k "cd /d %~dp0 && echo Starting API server... && py test_server_minimal.py && echo. && echo API server stopped. && pause"

timeout /t 5 /nobreak > nul

echo Step 3: Starting UI Server...
start "Sonora UI (Port 8501)" cmd /k "cd /d %~dp0 && echo Starting UI server... && py -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1 && echo. && echo UI server stopped. && pause"

echo.
echo ========================================
echo   Servers starting in separate windows
echo ========================================
echo.
echo Wait 30 seconds, then check:
echo   - API: http://127.0.0.1:8000/health
echo   - UI:  http://127.0.0.1:8501
echo.
echo Check the server windows for any error messages!
echo.
timeout /t 30 /nobreak > nul

echo.
echo Opening browser...
start http://127.0.0.1:8501

echo.
echo Done! Check the server windows and browser.
pause










