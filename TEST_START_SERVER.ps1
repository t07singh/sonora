# Test Server Start - Shows exactly what's happening
Write-Host ""
Write-Host "=== TESTING SERVER START ===" -ForegroundColor Cyan
Write-Host ""

$rootDir = "C:\Users\HP\.cursor"
$sonoraDir = "$rootDir\sonora"

Set-Location $sonoraDir

# Test 1: Check Python
Write-Host "Test 1: Python..." -ForegroundColor Yellow
try {
    $pyVersion = py --version 2>&1
    Write-Host "✓ $pyVersion" -ForegroundColor Green
} catch {
    Write-Host "✗ Python not found!" -ForegroundColor Red
    exit 1
}

# Test 2: Check dependencies
Write-Host ""
Write-Host "Test 2: Dependencies..." -ForegroundColor Yellow
try {
    py -c "import fastapi; import uvicorn; print('OK')" 2>&1 | Out-Null
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ FastAPI and Uvicorn installed" -ForegroundColor Green
    } else {
        Write-Host "✗ Missing dependencies!" -ForegroundColor Red
        Write-Host "   Installing..." -ForegroundColor Yellow
        py -m pip install fastapi uvicorn -q
    }
} catch {
    Write-Host "✗ Error checking dependencies" -ForegroundColor Red
}

# Test 3: Check if server file exists
Write-Host ""
Write-Host "Test 3: Server files..." -ForegroundColor Yellow
if (Test-Path "api\server.py") {
    Write-Host "✓ api\server.py exists" -ForegroundColor Green
} else {
    Write-Host "✗ api\server.py NOT FOUND" -ForegroundColor Red
    exit 1
}

if (Test-Path "run_server.py") {
    Write-Host "✓ run_server.py exists" -ForegroundColor Green
} else {
    Write-Host "⚠ run_server.py not found" -ForegroundColor Yellow
}

# Test 4: Try importing the server module
Write-Host ""
Write-Host "Test 4: Testing server import..." -ForegroundColor Yellow
$importTest = py -c "import sys; sys.path.insert(0, '.'); from api import server; print('Import OK')" 2>&1
if ($LASTEXITCODE -eq 0) {
    Write-Host "✓ Server imports successfully" -ForegroundColor Green
} else {
    Write-Host "✗ Server import FAILED!" -ForegroundColor Red
    Write-Host "Error output:" -ForegroundColor Yellow
    Write-Host $importTest -ForegroundColor Red
    Write-Host ""
    Write-Host "This is the problem! The server can't be imported." -ForegroundColor Yellow
    exit 1
}

# Test 5: Try starting server in background for 5 seconds
Write-Host ""
Write-Host "Test 5: Attempting to start server (5 second test)..." -ForegroundColor Yellow

$job = Start-Job -ScriptBlock {
    Set-Location "C:\Users\HP\.cursor\sonora"
    py -m uvicorn api.server:app --host 127.0.0.1 --port 8000 2>&1
}

Start-Sleep -Seconds 5

# Check if port is listening
$portCheck = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
if ($portCheck) {
    Write-Host "✓ Server started! Port 8000 is listening" -ForegroundColor Green
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
    Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
        Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    }
} else {
    Write-Host "✗ Server did NOT start" -ForegroundColor Red
    Write-Host "Job output:" -ForegroundColor Yellow
    Receive-Job $job -ErrorAction SilentlyContinue | Select-Object -First 10
    Stop-Job $job -ErrorAction SilentlyContinue
    Remove-Job $job -ErrorAction SilentlyContinue
}

Write-Host ""
Write-Host "=== TEST COMPLETE ===" -ForegroundColor Cyan
Write-Host ""













