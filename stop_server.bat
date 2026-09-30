@echo off
rem Stop the Reefmother servers (ports 8501 and 8502).
set FOUND=0
for %%n in (8501 8502) do (
  for /f "tokens=5" %%p in ('netstat -ano ^| findstr ":%%n" ^| findstr "LISTENING"') do (
    taskkill /PID %%p /F >nul 2>&1
    set FOUND=1
  )
)
if "%FOUND%"=="1" (
  echo Servers stopped.
) else (
  echo Servers were not running.
)
timeout /t 2 >nul
