# Final Working Sonora Launcher
Write-Host "Starting Sonora AI Dubbing System..." -ForegroundColor Cyan

# Start the simple server
Write-Host "Starting FastAPI backend on http://localhost:8000 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "py simple_server.py"

# Wait a bit for backend to start
Start-Sleep -Seconds 3

# Start Streamlit dashboard
Write-Host "Starting Streamlit dashboard on http://localhost:8501 ..." -ForegroundColor Yellow
Start-Process powershell -ArgumentList "-NoExit", "-Command", "py -m streamlit run ui/app.py --server.port 8501 --server.headless true"

# Wait a bit and open browser
Start-Sleep -Seconds 5
Write-Host "Opening dashboard in browser..." -ForegroundColor Cyan
Start-Process "http://localhost:8501"

Write-Host "`n✅ Sonora system launched successfully!" -ForegroundColor Green
Write-Host "   - FastAPI Backend:  http://localhost:8000" -ForegroundColor White
Write-Host "   - Streamlit Dashboard: http://localhost:8501" -ForegroundColor White
Write-Host "`n🎯 Ready to use! The dashboard should open in your browser." -ForegroundColor Green




