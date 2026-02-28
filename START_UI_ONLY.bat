@echo off
REM ============================================================
REM START SONORA UI ONLY (API may already be running)
REM ============================================================

cd /d "%~dp0sonora"

REM Ensure HOME environment variable is set (required for some components like browser/Playwright)
if "%HOME%"=="" (
    if not "%USERPROFILE%"=="" (
        set "HOME=%USERPROFILE%"
    ) else (
        set "HOME=%CD%"
    )
)

echo.
echo ============================================================
echo   🎨 STARTING SONORA UI
echo ============================================================
echo.

echo Starting Streamlit UI on port 8501...
start "Sonora UI" cmd /k "cd /d %~dp0sonora && echo ============================================================ && echo   SONORA UI SERVER (Port 8501) && echo ============================================================ && echo. && echo Starting UI... && echo. && .\venv\Scripts\python.exe -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1 && echo. && echo Server stopped. Press any key to close... && pause"

echo ✅ UI Server window opened
echo.
echo Waiting 10 seconds for UI to start...
timeout /t 10 >nul

echo.
echo ============================================================
echo   📍 ACCESS URL
echo ============================================================
echo.
echo    • Main UI:  http://127.0.0.1:8501
echo.
echo Opening browser...
timeout /t 2 >nul
start http://127.0.0.1:8501

echo.
echo ✅ Browser opened!
echo.
echo 💡 If you see connection refused:
echo    1. Wait 10-15 more seconds
echo    2. Refresh browser (F5)
echo    3. Check the "Sonora UI" window for errors
echo.
pause








