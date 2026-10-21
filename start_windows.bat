@echo off
cd /d "%~dp0"
if not exist ".venv\Scripts\python.exe" (
    echo FreeFIDS is not installed yet. Run install_windows.bat first.
    pause
    exit /b 1
)
".venv\Scripts\python.exe" app\launcher.py %*
