# ============================================================
# 🚀 SONORA LAUNCHER - DEBUG VERSION
# Shows actual errors and diagnostic info
# ============================================================

$ErrorActionPreference = "Continue"

Write-Host ""
Write-Host "🎌 Sonora Launcher (Debug Mode)" -ForegroundColor Cyan
Write-Host "=" * 60 -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path
Set-Location $ScriptDir

# Find Streamlit app
if (Test-Path "ui\app.py") {
    $streamlitApp = "app.py"
    $streamlitDir = Join-Path $ScriptDir "ui"
    Write-Host "✅ Found: ui\app.py" -ForegroundColor Green
} elseif (Test-Path "sonora\ui\demo_app.py") {
    $streamlitApp = "demo_app.py"
    $streamlitDir = Join-Path $ScriptDir "sonora\ui"
    Write-Host "✅ Found: sonora\ui\demo_app.py" -ForegroundColor Green
} else {
    Write-Host "❌ Streamlit app not found!" -ForegroundColor Red
    pause
    exit 1
}

# Test Streamlit directly
Write-Host ""
Write-Host "🧪 Testing Streamlit directly..." -ForegroundColor Yellow
Write-Host "   Working directory: $streamlitDir" -ForegroundColor Gray
Write-Host "   App file: $streamlitApp" -ForegroundColor Gray
Write-Host ""

# Check if port is in use
$port8501 = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue
if ($port8501) {
    Write-Host "⚠️  Port 8501 is in use by PID: $($port8501.OwningProcess)" -ForegroundColor Yellow
    $process = Get-Process -Id $port8501.OwningProcess -ErrorAction SilentlyContinue
    if ($process) {
        Write-Host "   Process: $($process.ProcessName) - $($process.Path)" -ForegroundColor Gray
        Write-Host "   Killing process..." -ForegroundColor Yellow
        Stop-Process -Id $port8501.OwningProcess -Force -ErrorAction SilentlyContinue
        Start-Sleep -Seconds 2
    }
}

# Start Streamlit in foreground to see errors
Write-Host ""
Write-Host "🚀 Starting Streamlit (you'll see output below)..." -ForegroundColor Cyan
Write-Host "   If you see errors, read them carefully!" -ForegroundColor Yellow
Write-Host "   Press Ctrl+C to stop" -ForegroundColor Yellow
Write-Host ""
Write-Host "=" * 60 -ForegroundColor Gray
Write-Host ""

Set-Location $streamlitDir

# Start backend first (in background)
Write-Host "Starting backend in background..." -ForegroundColor Gray
$backendProc = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$ScriptDir\sonora`"; py run_server.py" -PassThru -WindowStyle Minimized

# Now start Streamlit in this window (so we see errors)
try {
    py -m streamlit run $streamlitApp --server.port 8501 --server.address localhost --server.headless false
} catch {
    Write-Host ""
    Write-Host "❌ ERROR: $_" -ForegroundColor Red
    Write-Host ""
    Write-Host "Common issues:" -ForegroundColor Yellow
    Write-Host "1. Missing dependencies: pip install streamlit" -ForegroundColor White
    Write-Host "2. Import errors in app.py - check the error above" -ForegroundColor White
    Write-Host "3. Port conflict - another app using 8501" -ForegroundColor White
    pause
}
















