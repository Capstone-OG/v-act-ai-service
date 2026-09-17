@echo off
chcp 65001 > nul
set PYTHONIOENCODING=utf-8
echo Starting Conversational RAG CLI...
.venv\Scripts\python.exe main.py
pause
