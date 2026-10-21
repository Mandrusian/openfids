@echo off
setlocal EnableExtensions
cd /d "%~dp0"
title OpenFIDS installer
echo.
echo  OpenFIDS - installer for Windows
echo  ================================
echo.

call :findpy
if defined PY goto havepy

echo Python 3.9 or newer was not found. Installing it for you...
echo.
call :installpy
call :findpy
if defined PY goto havepy
echo.
echo Python was installed but could not be located.
echo Please close this window and run install_windows.bat once more.
pause
exit /b 1

:havepy
echo Using Python: %PY%
echo.
echo [1/3] Creating private environment ...
if exist ".venv\Scripts\python.exe" goto venvok
%PY% -m venv .venv
if errorlevel 1 goto fail
:venvok

echo [2/3] Installing requirements ...
".venv\Scripts\python.exe" -m pip install --upgrade pip >nul 2>nul
".venv\Scripts\python.exe" -m pip install -r app\requirements.txt
if errorlevel 1 goto fail

echo [3/3] Creating Desktop and Start menu shortcuts ...
call shortcut_windows.bat nopause
if errorlevel 1 goto fail

echo.
echo  All done! Starting OpenFIDS in your browser...
start "" ".venv\Scripts\pythonw.exe" "app\launcher.py"
echo.
echo  Next time, use the OpenFIDS shortcut on your Desktop or in the Start menu.
echo.
pause
exit /b 0

:fail
echo.
echo Something went wrong. Check your internet connection and run this again.
pause
exit /b 1

rem ---------------------------------------------------------------
rem :findpy  sets PY to a working Python 3.9+ (also checks the usual
rem install folders, because PATH is stale right after an install)
rem ---------------------------------------------------------------
:findpy
set "PY="
call :trypy py -3
if defined PY exit /b 0
call :trypy python
if defined PY exit /b 0
for %%V in (313 312 311 310 39) do (
  for %%D in ("%LocalAppData%\Programs\Python\Python%%V" "%ProgramFiles%\Python%%V") do (
    if not defined PY if exist "%%~D\python.exe" call :trypy "%%~D\python.exe"
  )
)
exit /b 0

:trypy
%* -c "import sys; sys.exit(0 if sys.version_info >= (3,9) else 1)" >nul 2>nul
if not errorlevel 1 set "PY=%*"
exit /b 0

rem ---------------------------------------------------------------
rem :installpy  winget first, then a direct download from python.org
rem ---------------------------------------------------------------
:installpy
where winget >nul 2>nul
if errorlevel 1 goto download
echo Installing Python 3.12 with winget. If Windows asks permission, click Yes.
winget install -e --id Python.Python.3.12 --silent --accept-source-agreements --accept-package-agreements
call :findpy
if defined PY exit /b 0

:download
echo Downloading Python from python.org ...
set "ARCH=amd64"
if /i "%PROCESSOR_ARCHITECTURE%"=="ARM64" set "ARCH=arm64"
if /i "%PROCESSOR_ARCHITEW6432%"=="ARM64" set "ARCH=arm64"
set "PYEXE=%TEMP%\openfids-python-setup.exe"
powershell -NoProfile -ExecutionPolicy Bypass -Command "[Net.ServicePointManager]::SecurityProtocol=[Net.SecurityProtocolType]::Tls12; Invoke-WebRequest -UseBasicParsing 'https://www.python.org/ftp/python/3.12.8/python-3.12.8-%ARCH%.exe' -OutFile '%PYEXE%'"
if errorlevel 1 exit /b 1
echo Installing Python (this takes a minute) ...
start /wait "" "%PYEXE%" /quiet InstallAllUsers=0 PrependPath=1 Include_test=0 Include_launcher=0
del "%PYEXE%" >nul 2>nul
exit /b 0
