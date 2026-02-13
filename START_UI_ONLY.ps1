# Start UI Only - Simple
Write-Host ""
Write-Host "=== STARTING SONORA UI ===" -ForegroundColor Cyan
Write-Host ""

# Clear port
Get-NetTCPConnection -LocalPort 8501 -ErrorAction SilentlyContinue | ForEach-Object {
    Stop-Process -Id $_.OwningProcess -Force -ErrorAction SilentlyContinue
}
Start-Sleep -Seconds 2

# Start UI
Write-Host "Starting Streamlit UI on port 8501..." -ForegroundColor Yellow
Write-Host "A new window will open - watch it for any errors!" -ForegroundColor Cyan
Write-Host ""

Start-Process powershell -ArgumentList "-NoExit", "-Command", `
    "cd C:\Users\HP\.cursor\sonora; `
    Write-Host ''; `
    Write-Host '========================================' -ForegroundColor Cyan; `
    Write-Host '  SONORA UI SERVER' -ForegroundColor Cyan; `
    Write-Host '  Port: 8501' -ForegroundColor Cyan; `
    Write-Host '========================================' -ForegroundColor Cyan; `
    Write-Host ''; `
    Write-Host 'Starting UI...' -ForegroundColor Yellow; `
    Write-Host 'If you see errors below, COPY THEM!' -ForegroundColor Yellow; `
    Write-Host ''; `
    py -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1; `
    Write-Host ''; `
    Write-Host 'Server stopped. Press any key to close...' -ForegroundColor Yellow; `
    pause"

Write-Host "Waiting 25 seconds for UI to start..." -ForegroundColor Gray
Start-Sleep -Seconds 25

# Test and open
Write-Host ""
Write-Host "Testing UI..." -ForegroundColor Yellow

try {
    $response = Invoke-WebRequest -Uri "http://127.0.0.1:8501" -UseBasicParsing -TimeoutSec 5
    Write-Host "✅ UI is running! Status: $($response.StatusCode)" -ForegroundColor Green
    Write-Host ""
    Write-Host "Opening browser..." -ForegroundColor Cyan
    Start-Sleep -Seconds 2
    Start-Process "http://127.0.0.1:8501"
} catch {
    Write-Host "⚠️ UI not responding yet" -ForegroundColor Yellow
    Write-Host ""
    Write-Host "IMPORTANT: Check the PowerShell window that opened!" -ForegroundColor Cyan
    Write-Host "   Look for any error messages (red text)" -ForegroundColor White
    Write-Host "   Common errors:" -ForegroundColor Yellow
    Write-Host "   - ModuleNotFoundError: Run 'py -m pip install streamlit'" -ForegroundColor Gray
    Write-Host "   - FileNotFoundError: Check if ui\demo_app.py exists" -ForegroundColor Gray
    Write-Host ""
    Write-Host "Opening browser anyway - refresh in 30 seconds if needed" -ForegroundColor Yellow
    Start-Process "http://127.0.0.1:8501"
}

Write-Host ""













