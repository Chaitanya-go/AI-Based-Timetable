@echo off
echo Starting Timetable Generator Backend...
cd backend
:: Execute from the virtual environment
.\venv\Scripts\python.exe -m uvicorn app.main:app --reload
pause
