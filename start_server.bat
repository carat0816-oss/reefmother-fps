@echo off
rem Start the Reefmother game (Streamlit) at http://localhost:8501
rem Run stop_server.bat or close this window to stop it.
cd /d "%~dp0"

netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo Server is already running. Opening browser...
  start "" http://localhost:8501
  timeout /t 3 >nul
  exit /b 0
)

echo Starting server at http://localhost:8501 ...
start "" /min powershell -NoProfile -Command "Start-Sleep 5; Start-Process 'http://localhost:8501'"
python -m streamlit run "%~dp0app.py" --server.port 8501 --server.headless true
if errorlevel 1 (
  echo.
  echo Failed to start. Install the requirements first:
  echo   python -m pip install -r requirements.txt
  pause
)
