@echo off
setlocal
cd /d "%~dp0"
if not exist ".venv\Scripts\pythonw.exe" (
    echo OpenFIDS is not installed yet. Run install_windows.bat first.
    pause
    exit /b 1
)
powershell -NoProfile -ExecutionPolicy Bypass -File "%~dp0app\make_shortcut.ps1" -Root "%~dp0."
if errorlevel 1 (
    echo Could not create the shortcuts.
    pause
    exit /b 1
)
echo Shortcuts created: Desktop and Start menu.
if /i not "%~1"=="nopause" pause
exit /b 0
