@echo off
cd /d "C:\Users\HP\.cursor\sonora"
venv\Scripts\python.exe -m streamlit run audio_editing\simple_editor_ui.py --server.port 8501 --server.headless true
pause























