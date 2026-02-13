@echo off
cd /d "%~dp0"
echo ========================================
echo   STARTING STREAMLIT (Visible Output)
echo ========================================
echo.
echo Current directory: %CD%
echo.
echo Starting Streamlit...
echo.
py -m streamlit run ui\demo_app.py --server.port 8501 --server.address 127.0.0.1
echo.
echo Streamlit stopped.
pause









