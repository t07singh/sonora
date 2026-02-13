# Check what errors might be occurring
Write-Host ""
Write-Host "=== DIAGNOSING SONORA STARTUP ISSUES ===" -ForegroundColor Cyan
Write-Host ""

# Check Python
Write-Host "1. Python Check:" -ForegroundColor Yellow
try {
    $py = py --version 2>&1
    Write-Host "   ✓ Python: $py" -ForegroundColor Green
} catch {
    Write-Host "   ✗ Python not found!" -ForegroundColor Red
    exit 1
}

# Check if we can import modules
Write-Host ""
Write-Host "2. Testing Imports:" -ForegroundColor Yellow
Write-Host "   Testing fastapi..." -ForegroundColor Gray
try {
    $null = py -c "import fastapi; print('OK')" 2>&1
    Write-Host "   ✓ fastapi works" -ForegroundColor Green
} catch {
    Write-Host "   ✗ fastapi import failed - Install: py -m pip install fastapi" -ForegroundColor Red
}

Write-Host "   Testing uvicorn..." -ForegroundColor Gray
try {
    $null = py -c "import uvicorn; print('OK')" 2>&1
    Write-Host "   ✓ uvicorn works" -ForegroundColor Green
} catch {
    Write-Host "   ✗ uvicorn import failed - Install: py -m pip install uvicorn" -ForegroundColor Red
}

Write-Host "   Testing streamlit..." -ForegroundColor Gray
try {
    $null = py -c "import streamlit; print('OK')" 2>&1
    Write-Host "   ✓ streamlit works" -ForegroundColor Green
} catch {
    Write-Host "   ✗ streamlit import failed - Install: py -m pip install streamlit" -ForegroundColor Red
}

# Check if app.main can be imported
Write-Host ""
Write-Host "3. Testing API Entry Point:" -ForegroundColor Yellow
cd C:\Users\HP\.cursor
Write-Host "   Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "   Testing app.main import..." -ForegroundColor Gray
try {
    $result = py -c "import sys; sys.path.insert(0, '.'); from app.main import app; print('OK')" 2>&1
    if ($result -match "OK") {
        Write-Host "   ✓ app.main imports successfully" -ForegroundColor Green
    } else {
        Write-Host "   ✗ app.main import failed:" -ForegroundColor Red
        Write-Host "   $result" -ForegroundColor Yellow
    }
} catch {
    Write-Host "   ✗ Error: $($_.Exception.Message)" -ForegroundColor Red
}

# Check UI file
Write-Host ""
Write-Host "4. Testing UI Entry Point:" -ForegroundColor Yellow
if (Test-Path "sonora\ui\demo_app.py") {
    Write-Host "   ✓ demo_app.py exists" -ForegroundColor Green
    Write-Host "   Testing streamlit syntax..." -ForegroundColor Gray
    try {
        $result = py -m py_compile "sonora\ui\demo_app.py" 2>&1
        Write-Host "   ✓ demo_app.py syntax is valid" -ForegroundColor Green
    } catch {
        Write-Host "   ✗ Syntax error in demo_app.py:" -ForegroundColor Red
        Write-Host "   $result" -ForegroundColor Yellow
    }
} else {
    Write-Host "   ✗ demo_app.py not found!" -ForegroundColor Red
}

# Check ports
Write-Host ""
Write-Host "5. Checking Ports:" -ForegroundColor Yellow
$port8000 = Get-NetTCPConnection -LocalPort 8000 -ErrorAction SilentlyContinue
$port8501 = Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue

if ($port8000) {
    Write-Host "   Port 8000: IN USE by PID $($port8000.OwningProcess)" -ForegroundColor Yellow
    $proc = Get-Process -Id $port8000.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "   Process: $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Gray
    }
} else {
    Write-Host "   Port 8000: FREE" -ForegroundColor Green
}

if ($port8501) {
    Write-Host "   Port 8501: IN USE by PID $($port8501.OwningProcess)" -ForegroundColor Yellow
    $proc = Get-Process -Id $port8501.OwningProcess -ErrorAction SilentlyContinue
    if ($proc) {
        Write-Host "   Process: $($proc.ProcessName) - $($proc.Path)" -ForegroundColor Gray
    }
} else {
    Write-Host "   Port 8501: FREE" -ForegroundColor Green
}

Write-Host ""
Write-Host "=== DIAGNOSTIC COMPLETE ===" -ForegroundColor Cyan
Write-Host ""
Write-Host "IMPORTANT: Check the PowerShell windows that opened!" -ForegroundColor Yellow
Write-Host "They will show the ACTUAL error messages preventing startup." -ForegroundColor Yellow
Write-Host ""
Write-Host "Common fixes based on errors:" -ForegroundColor Yellow
Write-Host "• ModuleNotFoundError → Run: py -m pip install <package-name>" -ForegroundColor White
Write-Host "• ImportError → Check file paths and Python path" -ForegroundColor White
Write-Host "• SyntaxError → Check Python file for syntax errors" -ForegroundColor White
Write-Host "• Address already in use → Kill process on that port" -ForegroundColor White
Write-Host ""














