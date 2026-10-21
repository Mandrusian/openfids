@echo off
setlocal
cd /d "%~dp0"
title FreeFIDS installer
echo.
echo  FreeFIDS - installer for Windows
echo  ================================
echo.

set "PY="
call :trypy py -3
if not defined PY call :trypy python
if not defined PY call :trypy "%LocalAppData%\Programs\Python\Python312\python.exe"
if not defined PY call :trypy "%LocalAppData%\Programs\Python\Python313\python.exe"
if defined PY goto havepy

echo Python 3.9 or newer was not found.
where winget >nul 2>nul
if errorlevel 1 goto nowinget
echo Installing Python 3.12 with winget. Accept any prompts that appear...
winget install -e --id Python.Python.3.12 --accept-source-agreements --accept-package-agreements
echo.
echo Python has been installed. Please CLOSE this window and run install_windows.bat again.
pause
exit /b 0

:nowinget
echo Please install Python from https://www.python.org/downloads/
echo Tick "Add python.exe to PATH" in the installer, then run this script again.
pause
exit /b 1

:havepy
echo Using Python: %PY%
echo.
echo [1/3] Creating private environment in .venv ...
if exist ".venv\Scripts\python.exe" goto venvok
%PY% -m venv .venv
if errorlevel 1 goto fail
:venvok

echo [2/3] Installing requirements ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r app\requirements.txt
if errorlevel 1 goto fail

echo [3/3] Creating shortcuts ...
call shortcut_windows.bat nopause

echo.
echo  All done! Use the "FreeFIDS" shortcut on your Desktop or Start menu.
echo  (Or double-click start_windows.bat.)
echo.
set /p LAUNCH="Start FreeFIDS now? [Y/n] "
if /i "%LAUNCH%"=="n" goto end
start "" ".venv\Scripts\pythonw.exe" "app\launcher.py"
:end
exit /b 0

:fail
echo.
echo Something went wrong. Check your internet connection and try again.
pause
exit /b 1

:trypy
%* -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0
