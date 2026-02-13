@echo off
cd /d "C:\Users\HP\.cursor\sonora"
echo ========================================
echo   SONORA UI SERVER (Port 8501)
echo ========================================
echo.
echo Starting Streamlit...
echo.
py -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1
echo.
echo Server stopped. Press any key to close...
pause










