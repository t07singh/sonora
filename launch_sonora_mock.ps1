# Sonora Mock Launcher
Write-Host "Starting Sonora AI Dubbing System (Mock Mode)..." -ForegroundColor Cyan

# Start the mock server with all endpoints
Write-Host "Starting Mock FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\HP\.cursor; py mock_sonora_server.py"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Streamlit dashboard
Write-Host "Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\HP\.cursor\sonora; py -m streamlit run ui/demo_app.py --server.port 8501 --server.headless true"

# Wait a bit and open browser
Start-Sleep -Seconds 5
Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
Start-Process "http://localhost:8501"

Write-Host "`n✅ Sonora system launched successfully (Mock Mode)!" -ForegroundColor Green
Write-Host "   - Mock FastAPI Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   - Streamlit Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "`n📋 Mock Mode Features:" -ForegroundColor Cyan
Write-Host "   - All API endpoints return sample data" -ForegroundColor White
Write-Host "   - Cache stats and metrics are simulated" -ForegroundColor White
Write-Host "   - Dashboard will work without errors" -ForegroundColor White
Write-Host "   - Upload functionality shows mock response" -ForegroundColor White
Write-Host "`nReady to explore! The dashboard should open in your browser." -ForegroundColor Green
