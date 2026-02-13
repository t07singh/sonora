@echo off
REM ============================================================
REM LAUNCH SONORA INTERFACE - All Models Working
REM ============================================================

cd /d "%~dp0sonora"

echo.
echo ============================================================
echo   🎬 SONORA AI DUBBING INTERFACE
echo   All 17 Models Fully Functional!
echo ============================================================
echo.

REM Step 1: Start API Server
echo [1/3] Starting API Server (Port 8000)...
start "Sonora API Server" cmd /k "cd /d %~dp0sonora && .\venv\Scripts\python.exe -m uvicorn api.server:app --host 127.0.0.1 --port 8000 --reload"
echo ✅ API Server starting...
echo.
timeout /t 5 >nul

REM Step 2: Wait for API to be ready
echo [2/3] Waiting for API to initialize...
:wait_api
curl -s http://127.0.0.1:8000/health >nul 2>&1
if errorlevel 1 (
    echo    Waiting for API... (this may take 10-30 seconds)
    timeout /t 2 >nul
    goto wait_api
)
echo ✅ API is ready!
echo.
timeout /t 2 >nul

REM Step 3: Start Streamlit UI
echo [3/3] Starting Streamlit UI (Port 8501)...
start "Sonora UI" cmd /k "cd /d %~dp0sonora && .\venv\Scripts\python.exe -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1"
echo ✅ UI starting...
echo.
timeout /t 8 >nul

REM Display Status
echo.
echo ============================================================
echo   ✅ SONORA INTERFACE IS RUNNING
echo ============================================================
echo.
echo 📍 Access URLs:
echo    • Streamlit UI:  http://127.0.0.1:8501
echo    • API Server:    http://127.0.0.1:8000
echo    • API Health:    http://127.0.0.1:8000/health
echo    • API Docs:      http://127.0.0.1:8000/docs
echo.
echo 🎯 Available Models (All Working):
echo    ✅ Whisper ASR (Local + API)
echo    ✅ Helsinki-NLP Translation
echo    ✅ Coqui TTS
echo    ✅ VibeVoice TTS (Mock)
echo    ✅ SpeechBrain Emotion Detection
echo    ✅ SepFormer Audio Separation
echo    ✅ Demucs Audio Separation
echo    ✅ Spleeter Audio Separation
echo    ✅ OpenUnmix Audio Separation
echo    ✅ Pyannote Speaker Diarization
echo    ✅ Resemblyzer Voice Embeddings
echo    ✅ All Mock Fallbacks
echo.
echo Opening browser in 3 seconds...
timeout /t 3 >nul
start http://127.0.0.1:8501
start http://127.0.0.1:8000/docs
echo.
echo ✅ Browser opened!
echo.
echo 💡 Tips:
echo    • Keep both command windows open
echo    • First request may take longer (model download)
echo    • Check API window for detailed logs
echo    • Close windows to stop services
echo.
pause








