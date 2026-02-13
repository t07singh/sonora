@echo off
echo ============================================================
echo   Starting Sonora Full Stack (API + UI)
echo ============================================================
echo.

REM Get the directory where this batch file is located
cd /d "%~dp0"

REM Check if sonora directory exists
if not exist "sonora" (
    echo ERROR: sonora directory not found!
    echo Please run this from the project root directory.
    pause
    exit /b 1
)

REM Method 1: Try app/main.py (root level)
if exist "app\main.py" (
    echo Starting API Server (app.main)...
    start "Sonora API Server" cmd /k "cd /d %~dp0 && py -m uvicorn app.main:app --host 0.0.0.0 --port 8000 --reload"
    echo API server window opened.
    timeout /t 5 >nul
)

REM Method 2: Try sonora/api/server.py
if not exist "app\main.py" (
    if exist "sonora\api\server.py" (
        echo Starting API Server (sonora/api/server)...
        start "Sonora API Server" cmd /k "cd /d %~dp0sonora && py -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload"
        echo API server window opened.
        timeout /t 5 >nul
    )
)

REM Method 3: Try sonora/run_server.py
if not exist "app\main.py" (
    if not exist "sonora\api\server.py" (
        if exist "sonora\run_server.py" (
            echo Starting API Server (run_server.py)...
            start "Sonora API Server" cmd /k "cd /d %~dp0sonora && py run_server.py"
            echo API server window opened.
            timeout /t 5 >nul
        )
    )
)

REM Start Streamlit UI
echo.
echo Starting Streamlit UI...
if exist "sonora\ui\demo_app.py" (
    start "Sonora UI" cmd /k "cd /d %~dp0sonora && py -m streamlit run ui\demo_app.py --server.port 8501"
    echo UI window opened.
) else if exist "ui\app.py" (
    start "Sonora UI" cmd /k "cd /d %~dp0 && py -m streamlit run ui\app.py --server.port 8501"
    echo UI window opened.
) else (
    echo WARNING: Could not find Streamlit app!
    echo Tried: sonora\ui\demo_app.py and ui\app.py
)

echo.
echo ============================================================
echo   Services Starting...
echo ============================================================
echo.
echo API Server: http://localhost:8000
echo API Health: http://localhost:8000/health
echo API Docs:   http://localhost:8000/docs
echo.
echo Streamlit UI: http://localhost:8501
echo.
echo Waiting 10 seconds for services to start...
timeout /t 10 >nul

echo.
echo Opening browser...
start http://localhost:8501

echo.
echo ============================================================
echo   Sonora Full Stack Launched!
echo ============================================================
echo.
echo Both services are running in separate windows.
echo Close those windows to stop the services.
echo.
pause

