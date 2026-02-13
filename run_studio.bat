@echo off
title SONORA AI STUDIO
echo ========================================
echo   🎬 SONORA AI DUBBING STUDIO
echo ========================================
echo.

REM 1. Run Diagnostics
python sonora/verify_connections.py
if %ERRORLEVEL% NEQ 0 (
    echo.
    echo [!] System diagnostics failed. Check requirements.
    pause
    exit /b %ERRORLEVEL%
)

echo.
echo [!] Launching Cockpit...
streamlit run sonora/app.py
pause