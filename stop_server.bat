@echo off
rem Stop the Reefmother server (whatever is listening on port 8501).
set FOUND=0
for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":8501" ^| findstr "LISTENING"') do (
  taskkill /PID %%p /F >nul 2>&1
  set FOUND=1
)
if "%FOUND%"=="1" (
  echo Server stopped.
) else (
  echo Server was not running.
)
timeout /t 2 >nul
