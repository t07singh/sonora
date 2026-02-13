# Comprehensive Diagnostic and Start Script
Write-Host ""
Write-Host "=== SONORA DIAGNOSTIC & START ===" -ForegroundColor Cyan
Write-Host ""

$rootDir = "C:\Users\HP\.cursor"
$sonoraDir = "$rootDir\sonora"

# Step 1: Check directory structure
Write-Host "Step 1: Checking directories..." -ForegroundColor Yellow
if (-not (Test-Path $sonoraDir)) {
    Write-Host "❌ ERROR: Sonora directory not found at $sonoraDir" -ForegroundColor Red
    exit 1
}
Write-Host "✓ Sonora directory exists" -ForegroundColor Green

# Step 2: Check for API server file
Write-Host ""
Write-Host "Step 2: Checking API server file..." -ForegroundColor Yellow
$apiFile = "$sonoraDir\api\server.py"
if (Test-Path $apiFile) {
    Write-Host "✓ API server file found: $apiFile" -ForegroundColor Green
} else {
    Write-Host "❌ ERROR: API server file NOT found!" -ForegroundColor Red
    Write-Host "   Expected: $apiFile" -ForegroundColor Yellow
    Write-Host "   Available files in api directory:" -ForegroundColor Yellow
    if (Test-Path "$sonoraDir\api") {
        Get-ChildItem "$sonoraDir\api" -Filter "*.py" | ForEach-Object { Write-Host "     - $($_.Name)" -ForegroundColor Gray }
    }
    exit 1
}

# Step 3: Check for UI file
Write-Host ""
Write-Host "Step 3: Checking UI file..." -ForegroundColor Yellow
$uiFile = "$sonoraDir\ui\app.py"
if (-not (Test-Path $uiFile)) {
    $uiFile = "$sonoraDir\ui\demo_app.py"
    if (-not (Test-Path $uiFile)) {
        Write-Host "❌ ERROR: UI file NOT found!" -ForegroundColor Red
        Write-Host "   Tried: ui\app.py and ui\demo_app.py" -ForegroundColor Yellow
        exit 1
    }
}
Write-Host "✓ UI file found: $uiFile" -ForegroundColor Green

# Step 4: Kill existing processes
Write-Host ""
Write-Host "Step 4: Clearing ports..." -ForegroundColor Yellow
$killed = 0
Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    $killed++
}
Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
    $killed++
}
if ($killed -gt 0) {
    Write-Host "✓ Killed $killed process(es) on ports 8000/8501" -ForegroundColor Green
    Start-Sleep -Seconds 2
} else {
    Write-Host "✓ Ports are free" -ForegroundColor Green
}

# Step 5: Test Python
Write-Host ""
Write-Host "Step 5: Testing Python..." -ForegroundColor Yellow
try {
    $pythonVersion = py --version 2>&1
    Write-Host "✓ Python found: $pythonVersion" -ForegroundColor Green
} catch {
    Write-Host "❌ ERROR: Python not found!" -ForegroundColor Red
    Write-Host "   Try: python --version or python3 --version" -ForegroundColor Yellow
    exit 1
}

# Step 6: Test imports
Write-Host ""
Write-Host "Step 6: Testing critical imports..." -ForegroundColor Yellow
try {
    $importTest = py -c "import fastapi; import uvicorn; import streamlit; print('OK')" 2>&1
    if ($LASTEXITCODE -eq 0) {
        Write-Host "✓ All required packages installed" -ForegroundColor Green
    } else {
        Write-Host "⚠️  Some packages may be missing. Error:" -ForegroundColor Yellow
        Write-Host $importTest -ForegroundColor Gray
        Write-Host ""
        Write-Host "Installing packages..." -ForegroundColor Yellow
        py -m pip install fastapi uvicorn streamlit -q
    }
} catch {
    Write-Host "⚠️  Could not test imports" -ForegroundColor Yellow
}

# Step 7: Start API server
Write-Host ""
Write-Host "Step 7: Starting API server..." -ForegroundColor Yellow
Write-Host "   Opening API window..." -ForegroundColor Gray

$apiScript = @"
cd `"$sonoraDir`"
Write-Host ''
Write-Host '=== SONORA API SERVER (Port 8000) ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting server...' -ForegroundColor Yellow
Write-Host ''
py -m uvicorn api.server:app --host 127.0.0.1 --port 8000
Write-Host ''
Write-Host 'Server stopped. Press any key to close...' -ForegroundColor Yellow
pause
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $apiScript -WindowStyle Normal

Write-Host "   Waiting 20 seconds for API to start..." -ForegroundColor Gray
Start-Sleep -Seconds 20

# Step 8: Test API
Write-Host ""
Write-Host "Step 8: Testing API connection..." -ForegroundColor Yellow
$apiOk = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8000/health" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✅ API is RUNNING!" -ForegroundColor Green
        Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Gray
        $apiOk = $true
        break
    } catch {
        Write-Host "   Attempt $i/3: API not responding yet..." -ForegroundColor Yellow
        if ($i -lt 3) {
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $apiOk) {
    Write-Host "⚠️  API not responding. Check the API window for errors." -ForegroundColor Yellow
    Write-Host "   Common issues:" -ForegroundColor Yellow
    Write-Host "   - Import errors (check API window)" -ForegroundColor Gray
    Write-Host "   - Port already in use" -ForegroundColor Gray
    Write-Host "   - Missing dependencies" -ForegroundColor Gray
}

# Step 9: Start UI server
Write-Host ""
Write-Host "Step 9: Starting UI server..." -ForegroundColor Yellow

$uiScript = @"
cd `"$sonoraDir`"
Write-Host ''
Write-Host '=== SONORA UI SERVER (Port 8501) ===' -ForegroundColor Cyan
Write-Host ''
Write-Host 'Starting UI...' -ForegroundColor Yellow
Write-Host ''
py -m streamlit run $(Split-Path $uiFile -Leaf) --server.port 8501 --server.address 127.0.0.1
Write-Host ''
Write-Host 'Server stopped. Press any key to close...' -ForegroundColor Yellow
pause
"@

Start-Process powershell -ArgumentList "-NoExit", "-Command", $uiScript -WindowStyle Normal

Write-Host "   Waiting 25 seconds for UI to start..." -ForegroundColor Gray
Start-Sleep -Seconds 25

# Step 10: Test UI
Write-Host ""
Write-Host "Step 10: Testing UI connection..." -ForegroundColor Yellow
$uiOk = $false
for ($i = 1; $i -le 3; $i++) {
    try {
        $response = Invoke-WebRequest -Uri "http://127.0.0.1:8501" -TimeoutSec 5 -UseBasicParsing -ErrorAction Stop
        Write-Host "✅ UI is RUNNING!" -ForegroundColor Green
        Write-Host "   Status: $($response.StatusCode)" -ForegroundColor Gray
        $uiOk = $true
        break
    } catch {
        Write-Host "   Attempt $i/3: UI not responding yet..." -ForegroundColor Yellow
        if ($i -lt 3) {
            Start-Sleep -Seconds 5
        }
    }
}

if (-not $uiOk) {
    Write-Host "⚠️  UI not responding. Check the UI window for errors." -ForegroundColor Yellow
}

# Final summary
Write-Host ""
Write-Host "=== SUMMARY ===" -ForegroundColor Cyan
Write-Host ""

if ($apiOk) {
    Write-Host "✅ API: http://127.0.0.1:8000" -ForegroundColor Green
    Write-Host "   Health: http://127.0.0.1:8000/health" -ForegroundColor Gray
    Write-Host "   Docs: http://127.0.0.1:8000/docs" -ForegroundColor Gray
} else {
    Write-Host "❌ API: Not responding" -ForegroundColor Red
    Write-Host "   Check the API PowerShell window for errors" -ForegroundColor Yellow
}

if ($uiOk) {
    Write-Host "✅ UI: http://127.0.0.1:8501" -ForegroundColor Green
} else {
    Write-Host "❌ UI: Not responding" -ForegroundColor Red
    Write-Host "   Check the UI PowerShell window for errors" -ForegroundColor Yellow
}

Write-Host ""

if ($apiOk -and $uiOk) {
    Write-Host "🎉 SUCCESS! Opening browser..." -ForegroundColor Green
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8501"
    Start-Sleep -Seconds 1
    Start-Process "http://127.0.0.1:8000/docs"
} else {
    Write-Host "⚠️  Some services failed to start" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "Next steps:" -ForegroundColor Cyan
    Write-Host "1. Check the PowerShell windows that opened for error messages" -ForegroundColor White
    Write-Host "2. Copy any error messages you see" -ForegroundColor White
    Write-Host "3. Try manually starting:" -ForegroundColor White
    Write-Host ""
    Write-Host "   API: cd $sonoraDir; py -m uvicorn api.server:app --host 127.0.0.1 --port 8000" -ForegroundColor Gray
    Write-Host "   UI:  cd $sonoraDir; py -m streamlit run $(Split-Path $uiFile -Leaf) --server.port 8501" -ForegroundColor Gray
}

Write-Host ""













