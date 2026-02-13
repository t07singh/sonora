# Start Streamlit UI in a new window
cd C:\Users\HP\.cursor\sonora
Start-Process powershell -ArgumentList "-NoExit", "-Command", "cd C:\Users\HP\.cursor\sonora; Write-Host '=== SONORA STREAMLIT UI ===' -ForegroundColor Cyan; Write-Host ''; py -m streamlit run ui\demo_app.py --server.port 8501; Write-Host ''; Write-Host 'UI stopped. Press any key...' -ForegroundColor Yellow; pause"

