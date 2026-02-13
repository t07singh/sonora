# Sonora Demo Interface Launcher
Write-Host ""
Write-Host "Starting Sonora Demo Interface..." -ForegroundColor Cyan
Write-Host "==================================================" -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Check if sonora directory exists
if (-not (Test-Path "sonora")) {
    Write-Host "Error: sonora directory not found!" -ForegroundColor Red
    Write-Host "Please run this script from the project root." -ForegroundColor Yellow
    pause
    exit 1
}

# Check if demo app exists
if (-not (Test-Path "sonora\ui\demo_app.py")) {
    Write-Host "Error: demo_app.py not found!" -ForegroundColor Red
    Write-Host "Expected location: sonora\ui\demo_app.py" -ForegroundColor Yellow
    pause
    exit 1
}

# Kill any existing Streamlit on port 8501
Write-Host "Checking port 8501..." -ForegroundColor Yellow
$port8501 = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if ($port8501) {
    Write-Host "   Found process on port 8501, stopping..." -ForegroundColor Gray
    Stop-Process -Id $port8501.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start Backend (in separate window)
Write-Host ""
Write-Host "Starting FastAPI backend..." -ForegroundColor Yellow
Write-Host "   This will open in a new PowerShell window" -ForegroundColor Gray

$backendCommand = "cd '$ScriptDir'; Write-Host 'Sonora FastAPI Backend - Port 8000' -ForegroundColor Cyan; Write-Host '==================================================' -ForegroundColor Cyan; cd sonora; if (Test-Path 'run_server.py') { py run_server.py } elseif (Test-Path 'api\server.py') { py -m uvicorn api.server:app --host 0.0.0.0 --port 8000 --reload } else { Write-Host 'Could not find server file!' -ForegroundColor Red; pause }"

$backendWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", $backendCommand -PassThru -WindowStyle Normal

Write-Host "Backend window opened" -ForegroundColor Green
Write-Host "   Waiting 5 seconds for backend to start..." -ForegroundColor Gray
Start-Sleep -Seconds 5

# Start Streamlit Demo (in separate window)
Write-Host ""
Write-Host "Starting Streamlit Demo Interface..." -ForegroundColor Yellow
Write-Host "   This will open in a new PowerShell window" -ForegroundColor Gray

$streamlitCommand = "cd '$ScriptDir\sonora'; Write-Host 'Sonora Demo Interface - Port 8501' -ForegroundColor Cyan; Write-Host '==================================================' -ForegroundColor Cyan; py -m streamlit run ui\demo_app.py --server.port 8501 --server.headless true"

$streamlitWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", $streamlitCommand -PassThru -WindowStyle Normal

Write-Host "Demo interface window opened" -ForegroundColor Green
Write-Host "   Waiting 3 seconds for Streamlit to start..." -ForegroundColor Gray
Start-Sleep -Seconds 3

# Open browser
Write-Host ""
Write-Host "Opening demo interface in browser..." -ForegroundColor Cyan
Start-Sleep -Seconds 2
Start-Process "http://localhost:8501"

Write-Host ""
Write-Host "==================================================" -ForegroundColor Green
Write-Host "Sonora Demo Interface Launched Successfully!" -ForegroundColor Green
Write-Host "==================================================" -ForegroundColor Green
Write-Host ""
Write-Host "Access URLs:" -ForegroundColor White
Write-Host "   Demo Interface:  http://localhost:8501" -ForegroundColor Cyan
Write-Host "   FastAPI Backend: http://localhost:8000" -ForegroundColor Cyan
Write-Host "   API Documentation: http://localhost:8000/docs" -ForegroundColor Cyan
Write-Host ""
Write-Host "Tips:" -ForegroundColor Yellow
Write-Host "   Check API health in the sidebar" -ForegroundColor White
Write-Host "   Upload a WAV/MP3/M4A file to start" -ForegroundColor White
Write-Host "   Monitor cache stats in real-time" -ForegroundColor White
Write-Host "   Enable auto-refresh for live metrics" -ForegroundColor White
Write-Host ""
Write-Host "The demo interface should now be open in your browser!" -ForegroundColor Green
Write-Host ""
Write-Host "Press any key to exit this launcher (the demo will keep running)..." -ForegroundColor Gray
$null = $Host.UI.RawUI.ReadKey("NoEcho,IncludeKeyDown")
