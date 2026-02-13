@echo off
echo ========================================
echo Sonora Model Dependencies Installer
echo ========================================
echo.

cd /d "%~dp0"

echo [1/12] Installing PyTorch (CPU)...
call venv\Scripts\python.exe -m pip install torch --index-url https://download.pytorch.org/whl/cpu
if errorlevel 1 (
    echo ERROR: PyTorch installation failed
    pause
    exit /b 1
)

echo.
echo [2/12] Installing Transformers...
call venv\Scripts\python.exe -m pip install transformers sentencepiece sacremoses
if errorlevel 1 (
    echo ERROR: Transformers installation failed
    pause
    exit /b 1
)

echo.
echo [3/12] Installing Coqui TTS...
call venv\Scripts\python.exe -m pip install numpy==1.23.5
call venv\Scripts\python.exe -m pip install TTS==0.22.0
if errorlevel 1 (
    echo ERROR: Coqui TTS installation failed
    pause
    exit /b 1
)

echo.
echo [4/12] Installing VibeVoice...
call venv\Scripts\python.exe -m pip install vibevoice
if errorlevel 1 (
    echo WARNING: VibeVoice installation failed - will use mock mode
)

echo.
echo [5/12] Installing SpeechBrain...
call venv\Scripts\python.exe -m pip install speechbrain
if errorlevel 1 (
    echo ERROR: SpeechBrain installation failed
    pause
    exit /b 1
)

echo.
echo [6/12] Installing Demucs...
call venv\Scripts\python.exe -m pip install demucs==4.0.0
if errorlevel 1 (
    echo ERROR: Demucs installation failed
    pause
    exit /b 1
)

echo.
echo [7/12] Installing Spleeter...
call venv\Scripts\python.exe -m pip install tensorflow-cpu==2.12.0
call venv\Scripts\python.exe -m pip install spleeter
if errorlevel 1 (
    echo WARNING: Spleeter installation failed - will use fallback
)

echo.
echo [8/12] Installing Open-Unmix...
call venv\Scripts\python.exe -m pip install openunmix
if errorlevel 1 (
    echo WARNING: Open-Unmix installation failed - will use fallback
)

echo.
echo [9/12] Installing Pyannote Audio...
echo NOTE: You need to set PYANNOTE_TOKEN environment variable first!
call venv\Scripts\python.exe -m pip install pyannote.audio
if errorlevel 1 (
    echo WARNING: Pyannote installation failed - will use mock mode
)

echo.
echo [10/12] Installing Resemblyzer...
call venv\Scripts\python.exe -m pip install resemblyzer
if errorlevel 1 (
    echo ERROR: Resemblyzer installation failed
    pause
    exit /b 1
)

echo.
echo [11/12] Installing Audio Libraries...
call venv\Scripts\python.exe -m pip install soundfile librosa ffmpeg-python audioread
if errorlevel 1 (
    echo WARNING: Some audio libraries failed - may affect functionality
)

echo.
echo [12/12] Verifying installations...
call venv\Scripts\python.exe -m pip list | findstr /i "torch transformers TTS speechbrain demucs spleeter openunmix pyannote resemblyzer"

echo.
echo ========================================
echo Installation Complete!
echo ========================================
echo.
echo Next steps:
echo 1. Set PYANNOTE_TOKEN if you want diarization: setx PYANNOTE_TOKEN "YOUR_TOKEN"
echo 2. Run the inspector: python ..\sonora_inspector.py
echo 3. Start Sonora: python run_full.py
echo.
pause








