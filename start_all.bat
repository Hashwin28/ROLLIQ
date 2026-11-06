@echo off
title Launch ROLLIQ System
echo ========================================================
echo    ROLLIQ - Smart Bed-Mobility Monitoring System
echo        Starting Backend and Frontend in Parallel
echo ========================================================
echo.

start "ROLLIQ Backend" cmd /k "%~dp0run_backend.bat"
timeout /t 3 /nobreak > nul
start "ROLLIQ Frontend" cmd /k "%~dp0run_frontend.bat"

echo.
echo Both services launched!
echo - Backend:  http://localhost:8000 (API & Docs at /docs)
echo - Frontend: http://localhost:3000
echo.
pause
