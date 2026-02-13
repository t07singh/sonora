@echo off
setlocal EnableDelayedExpansion

REM INSTALL SONORA B2B APPLIANCE (Windows)
REM v1.0.0

echo ===================================
echo   🚀 INITIALIZING SONORA INSTALLER
echo ===================================
echo.

REM 1. System Checks
echo Checking prerequisites...
docker --version >nul 2>&1
if %errorlevel% neq 0 (
    echo ❌ Docker is not installed or not in PATH.
    echo Please install Docker Desktop for Windows.
    pause
    exit /b 1
)
echo ✅ Docker found.
echo.

REM 1.5 Hardware Pre-Flight Check (GPU)
echo Checking GPU capabilities...
nvidia-smi >nul 2>&1
if %errorlevel% neq 0 (
    echo ⚠️  NVIDIA GPU not detected.
    echo    Visual Sync (Wav2Lip-HQ) will run in CPU-Legacy mode (Slow).
    echo.
) else (
    echo ✅ NVIDIA GPU detected.
    nvidia-smi --query-gpu=name,memory.total --format=csv,noheader
)
echo.

REM 2. Configuration Challenge
if not exist .env (
    echo ⚠️  No .env file found. Configuring Production Secrets.
    echo.
    set /p SONORA_KEY="Enter your SONORA_API_KEY (Admin Access): "
    set /p OPENAI_KEY="Enter OPENAI_API_KEY: "
    set /p ELEVEN_KEY="Enter ELEVENLABS_API_KEY: "
    
    (
        echo SONORA_API_KEY=!SONORA_KEY!
        echo OPENAI_API_KEY=!OPENAI_KEY!
        echo ELEVENLABS_API_KEY=!ELEVEN_KEY!
        echo SONORA_DATA_DIR=./sonora/data
        echo LOG_LEVEL=INFO
    ) > .env
    echo ✅ Configuration saved to .env
) else (
    echo ✅ existing .env found. Using it.
)

REM 3. Launch
echo.
echo 🚢 Deploying Production Stack...
docker compose -f docker-compose.prod.yml up -d --build

echo.
echo ===================================
echo   🎉 SONORA IS LIVE!
echo ===================================
echo    Dashboard: http://localhost:8501
echo    API:       http://localhost:8000
echo.
echo Close this window to keep running in background.
pause
