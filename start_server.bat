@echo off
rem Start the Reefmother game.
rem   8501 : Streamlit page (game embedded)
rem   8502 : game page alone (full window, mouse lock works)
rem Run stop_server.bat to stop both.
cd /d "%~dp0"

netstat -ano | findstr ":8502" | findstr "LISTENING" >nul
if errorlevel 1 (
  echo Starting game page server at http://localhost:8502/game.html ...
  start "reef-game-8502" /min python -m http.server 8502 --bind 127.0.0.1 --directory "%~dp0static"
)

netstat -ano | findstr ":8501" | findstr "LISTENING" >nul
if %errorlevel%==0 (
  echo Streamlit is already running. Opening browser...
  start "" http://localhost:8501
  timeout /t 3 >nul
  exit /b 0
)

echo Starting Streamlit at http://localhost:8501 ...
start "" /min powershell -NoProfile -Command "Start-Sleep 5; Start-Process 'http://localhost:8501'"
python -m streamlit run "%~dp0app.py" --server.port 8501 --server.headless true
if errorlevel 1 (
  echo.
  echo Failed to start. Check that Python and Streamlit are installed:
  echo   python -m pip install streamlit
  pause
)
