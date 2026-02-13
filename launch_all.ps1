# Complete Launcher - Backend + Streamlit
Write-Host ""
Write-Host "🎌 Starting Sonora (Backend + Dashboard)..." -ForegroundColor Cyan
Write-Host ""

$ScriptDir = Split-Path -Parent $MyInvocation.MyCommand.Path

# Start Backend
Write-Host "🚀 Starting Backend (port 8000)..." -ForegroundColor Yellow
$backend = Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd `"$ScriptDir\sonora`"; py run_server.py" -PassThru -WindowStyle Normal
Start-Sleep -Seconds 8

# Start Streamlit  
Write-Host "🎬 Starting Dashboard (port 8501)..." -ForegroundColor Yellow
$streamlit = Start-Process powershell -ArgumentList "-File", "`"$ScriptDir\start_streamlit.ps1`"" -PassThru -WindowStyle Normal

Write-Host ""
Write-Host "✅ Both services starting..." -ForegroundColor Green
Write-Host "   Backend window: FastAPI on port 8000" -ForegroundColor Gray
Write-Host "   Streamlit window: Dashboard on port 8501" -ForegroundColor Gray
Write-Host ""
Write-Host "⏳ Wait 20-30 seconds, then:" -ForegroundColor Yellow
Write-Host "   1. Check Streamlit window for 'You can now view...'" -ForegroundColor White
Write-Host "   2. Open: http://localhost:8501" -ForegroundColor White
Write-Host ""
Write-Host "💡 If connection refused:" -ForegroundColor Cyan
Write-Host "   • Wait longer (first start takes time)" -ForegroundColor White
Write-Host "   • Check Streamlit window for errors" -ForegroundColor White
Write-Host "   • Refresh browser after 30 seconds" -ForegroundColor White
Write-Host ""
















