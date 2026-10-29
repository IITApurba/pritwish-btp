@echo off
setlocal
rem One-time setup for Windows: creates .venv in the project folder and installs the requirements.
rem run.bat calls this with --no-pause so the window does not stop before the app starts.
cd /d "%~dp0.."
if /i "%~1"=="--no-pause" set NOPAUSE=1

rem Find Python 3.9+. The "py" launcher is preferred; "python" may be the Microsoft Store stub, so test it.
set PY=
where py >nul 2>nul && set "PY=py -3"
if not defined PY where python >nul 2>nul && set "PY=python"
if not defined PY goto nopython
%PY% -c "import sys; sys.exit(sys.version_info < (3, 9))" >nul 2>nul
if errorlevel 1 goto nopython

rem Create .venv, or rebuild it if it is missing or broken.
.venv\Scripts\python.exe -c "import sys" >nul 2>nul
if errorlevel 1 (
  echo Creating virtual environment...
  %PY% -m venv --clear .venv
  if errorlevel 1 goto fail
)

echo Installing requirements, this can take a few minutes...
.venv\Scripts\python.exe -m pip install --upgrade pip
.venv\Scripts\python.exe -m pip install -r requirements.txt
if errorlevel 1 goto fail

echo.
echo Setup complete. Now double-click windows\run.bat to start the app.
if not defined NOPAUSE pause
exit /b 0

:nopython
echo Python 3.9 or newer was not found. Install it from https://www.python.org/downloads/
echo and tick "Add python.exe to PATH" in the installer, then run this again.
if not defined NOPAUSE pause
exit /b 1

:fail
echo.
echo Setup failed. Check your internet connection and the messages above, then run this again.
if not defined NOPAUSE pause
exit /b 1
