@echo off
title Sonora UI Server
cd /d "%~dp0"
echo ========================================
echo   SONORA UI SERVER
echo ========================================
echo.
echo Starting Streamlit...
echo.
echo If you see errors below, please share them!
echo.
py -m streamlit run ui\demo_app_simple.py --server.port 8501 --server.address 127.0.0.1 --server.headless true
echo.
echo.
echo Server stopped. Press any key to close...
pause > nul









