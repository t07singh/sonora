@echo off
echo ========================================
echo Sonora Studio Emergency Reboot
echo ========================================
echo.
echo Stopping any running uvicorn processes...
taskkill /f /fi "imagename eq uvicorn.exe" /fi "imagename eq python.exe" /v | findstr /i "api.server"

echo.
echo Cleaning up environment...
set CLOUD_OFFLOAD=true

echo.
echo Restarting Sonora API Server...
echo.
start "Sonora Backend Server" START_SERVER_NOW.bat

echo.
echo ========================================
echo Backend Restarted. Please try the 
echo Neural Slicing dissection again.
echo ========================================
pause
