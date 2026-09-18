@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo ============================================================
echo   Starting V-Act AI Service (FastAPI Server)
echo   Swagger UI: http://localhost:8000/docs
echo ============================================================
.venv\Scripts\python.exe main.py
pause
