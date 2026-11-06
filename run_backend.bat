@echo off
title ROLLIQ Backend Server
cd /d "%~dp0\backend"
echo ========================================================
echo    ROLLIQ - Smart Bed-Mobility Monitoring System
echo              Starting FastAPI Backend Server
echo ========================================================
echo.
python -m uvicorn main:app --host 0.0.0.0 --port 8000 --reload
pause
