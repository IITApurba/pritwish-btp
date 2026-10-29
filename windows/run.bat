@echo off
rem Starts the web app on Windows and opens it in the browser.
cd /d "%~dp0.."

if not exist .venv\Scripts\python.exe (
  echo Setup has not been run yet - running it now.
  call windows\setup.bat
  if not exist .venv\Scripts\python.exe exit /b 1
)

echo Starting the app at http://127.0.0.1:5001  (press Ctrl+C to stop)
start "" /b cmd /c "timeout /t 3 >nul & start http://127.0.0.1:5001"
.venv\Scripts\python.exe app.py
pause
