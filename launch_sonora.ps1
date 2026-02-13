# ============================================================
# 🚀 SONORA LAUNCHER - FIXED VERSION
# This version shows errors and waits properly
# ============================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "🎌 Sonora AI Dubbing System" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Find Streamlit app
if (Test-Path "ui\app.py") {
    $streamlitApp = "app.py"
    $streamlitDir = "$ScriptDir\ui"
    Write-Host "✅ Found: ui\app.py" -ForegroundColor Green
} elseif (Test-Path "sonora\ui\demo_app.py") {
    $streamlitApp = "demo_app.py"
    $streamlitDir = "$ScriptDir\sonora\ui"
    Write-Host "✅ Found: sonora\ui\demo_app.py" -ForegroundColor Green
} else {
    Write-Host "❌ Streamlit app not found!" -ForegroundColor Red
    pause
    exit 1
}

# Kill port 8501
Write-Host ""
Write-Host "🧹 Cleaning port 8501..." -ForegroundColor Yellow
$port8501 = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if ($port8501) {
    Write-Host "   Killing process on port 8501..." -ForegroundColor Gray
    Stop-Process -Id $port8501.OwningProcess -Force -ErrorAction SilentlyContinue
    Start-Sleep -Seconds 2
}

# Start Backend (in separate window)
Write-Host ""
Write-Host "🚀 Starting FastAPI backend..." -ForegroundColor Yellow
$backendWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$ScriptDir\sonora`"; Write-Host 'FastAPI Backend - Port 8000' -ForegroundColor Cyan; py run_server.py" -PassThru -WindowStyle Normal
Write-Host "✅ Backend window opened" -ForegroundColor Green
Start-Sleep -Seconds 5

# Start Streamlit (in separate window, visible so we see errors)
Write-Host ""
Write-Host "🎬 Starting Streamlit dashboard..." -ForegroundColor Yellow
Write-Host "   This will open in a new window - watch for errors!" -ForegroundColor Gray
Write-Host ""

Set-Location $streamlitDir

# Start Streamlit in new window so we can see output
$streamlitWindow = Start-Process powershell -ArgumentList "-NoExit", "-Command", @"
cd `"$streamlitDir`"
Write-Host '========================================' -ForegroundColor Cyan
Write-Host '  STREAMLIT DASHBOARD - Port 8501' -ForegroundColor Green
Write-Host '========================================' -ForegroundColor Cyan
Write-Host ''
Write-Host 'If you see errors below, please read them!' -ForegroundColor Yellow
Write-Host ''
py -m streamlit run $streamlitApp --server.port 8501 --server.address localhost --server.headless false
Write-Host ''
Write-Host 'Streamlit stopped. Press any key to close...' -ForegroundColor Yellow
pause
"@ -PassThru -WindowStyle Normal

Set-Location $ScriptDir

Write-Host "✅ Streamlit window opened" -ForegroundColor Green
Write-Host ""

# Wait for Streamlit - check more carefully
Write-Host "⏳ Waiting for Streamlit to start..." -ForegroundColor Yellow
Write-Host "   (Watch the Streamlit window for status)" -ForegroundColor Gray
Write-Host ""

$maxWait = 60
$attempt = 0
$ready = $false

while ($attempt -lt $maxWait) {
    Start-Sleep -Seconds 2
    $attempt += 2
    
    try {
        $response = Invoke-WebRequest -Uri "http://localhost:8501" -TimeoutSec 1 -ErrorAction SilentlyContinue -UseBasicParsing
        if ($response.StatusCode -eq 200) {
            $ready = $true
            Write-Host "✅ Streamlit is READY! (waited $attempt seconds)" -ForegroundColor Green
            break
        }
    } catch {
        # Still waiting
        if ($attempt % 10 -eq 0) {
            Write-Host "   Still waiting... ($attempt/$maxWait seconds)" -ForegroundColor Gray
            Write-Host "   Check the Streamlit window for errors!" -ForegroundColor Yellow
        }
    }
}

# Open browser
Write-Host ""
if ($ready) {
    Write-Host "🌐 Opening browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://localhost:8501"
} else {
    Write-Host "⚠️  Streamlit didn't respond after $maxWait seconds" -ForegroundColor Yellow
    Write-Host "   Opening browser anyway - please check:" -ForegroundColor Yellow
    Write-Host "   1. Look at the Streamlit window for errors" -ForegroundColor White
    Write-Host "   2. Try refreshing the browser" -ForegroundColor White
    Write-Host "   3. Wait 30 more seconds and refresh" -ForegroundColor White
    Start-Process "http://localhost:8501"
}

Write-Host ""
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host "✅ LAUNCH COMPLETE!" -ForegroundColor Green
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""
Write-Host "📍 Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "📍 API:       http://localhost:8000" -ForegroundColor White
Write-Host ""
Write-Host "💡 IMPORTANT:" -ForegroundColor Yellow
Write-Host "   • Check the Streamlit window for any errors" -ForegroundColor White
Write-Host "   • If you see import errors, run: py -m pip install streamlit requests" -ForegroundColor White
Write-Host "   • If connection refused, wait 30 seconds and refresh browser" -ForegroundColor White
Write-Host ""
Write-Host "🛑 To stop: Close the PowerShell windows" -ForegroundColor Yellow
Write-Host ""
