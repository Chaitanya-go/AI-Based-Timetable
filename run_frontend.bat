@echo off
setlocal
echo 1. Stopping any other projects...
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5173') do taskkill /F /PID %%a 2>nul
for /f "tokens=5" %%a in ('netstat -ano ^| findstr :5174') do taskkill /F /PID %%a 2>nul

echo 2. Navigating to Frontend directory...
cd /d "C:\Users\Chaitanya\.gemini\antigravity\playground\Timetable\frontend"

echo 3. Starting Timetable Generator on Port 5174...
call npm.cmd run dev
pause
