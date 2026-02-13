# Direct UI Starter - Shows all errors
Write-Host ""
Write-Host "=== Starting Sonora UI Directly ===" -ForegroundColor Cyan
Write-Host ""

cd C:\Users\HP\.cursor\sonora

Write-Host "Current directory: $(Get-Location)" -ForegroundColor Gray
Write-Host "Checking demo_app.py..." -ForegroundColor Yellow

if (Test-Path "ui\demo_app.py") {
    Write-Host "✓ File exists: ui\demo_app.py" -ForegroundColor Green
} else {
    Write-Host "✗ File NOT FOUND: ui\demo_app.py" -ForegroundColor Red
    Write-Host "Available files:" -ForegroundColor Yellow
    Get-ChildItem -Path "ui" -Filter "*.py" | ForEach-Object { Write-Host "  - $($_.Name)" -ForegroundColor Gray }
    pause
    exit 1
}

Write-Host ""
Write-Host "Starting Streamlit..." -ForegroundColor Yellow
Write-Host "Watch this window for errors!" -ForegroundColor Yellow
Write-Host ""

# Start Streamlit directly in this window so we can see errors
py -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1 --server.headless false














