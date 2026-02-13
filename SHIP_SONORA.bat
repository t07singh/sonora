@echo off
title 🚢 SHIPPING SONORA: AI DUBBING STUDIO
echo ============================================================
echo   🚢 SHIPPING SONORA: AI DUBBING STUDIO (CONVERGENCE v5.2)
echo ============================================================
echo.

echo [1/4] PRE-FLIGHT CHECK: NVIDIA BRIDGE (GPU PASSTHROUGH)
echo ------------------------------------------------------------
docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi >nul 2>&1
if errorlevel 1 (
    echo ⚠️  NVIDIA GPU NOT DETECTED IN DOCKER RUNTIME!
    echo    Please ensure:
    echo    1. NVIDIA Drivers (515+) are installed.
    echo    2. WSL 2 is the default engine in Docker Settings.
    echo    3. NVIDIA Container Toolkit is installed.
    echo.
    set /p continue="Continue in CPU-HARDENED mode? (y/n): "
    if /i not "%continue%"=="y" exit /b 1
) else (
    echo ✅ NVIDIA Hardware Handshake: SUCCESSFUL.
    docker run --rm --gpus all nvidia/cuda:12.0-base-ubuntu22.04 nvidia-smi
)
echo.

echo [2/4] ORCHESTRATING CONTAINER SWARM...
docker-compose up --build -d

echo.
echo [3/4] WAITING FOR SWARM HANDSHAKE...
:wait_api
curl -s http://localhost:8000/health >nul 2>&1
if errorlevel 1 (
    echo    Waiting for Sonora Core Swarm... [retry in 2s]
    timeout /t 2 >nul
    goto wait_api
)

echo.
echo [4/4] FINALIZING STUDIO WORKSPACE...
timeout /t 2 >nul

echo.
echo ============================================================
echo   ✅ SONORA CONVERGENCE COMPLETE
echo ============================================================
echo.
echo   📍 Studio Cockpit: http://localhost:8501
echo   📍 Redis HUD Feed:  http://localhost:6379 (Internal)
echo.
echo   [Swarm: Transcriber + Separator + Synthesizer + Redis]
echo.
echo   Press any key to close this orchestrator...
pause > nul
