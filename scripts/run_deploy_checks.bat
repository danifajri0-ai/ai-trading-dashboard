@echo off
setlocal

cd /d "%~dp0\.."

set "VENV_DIR=venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

if not exist "%PYTHON_EXE%" (
    echo ERROR: Virtual environment not found. Run the setup steps first.
    pause
    exit /b 1
)

"%PYTHON_EXE%" scripts\check_deploy_ready.py
if errorlevel 1 (
    echo.
    echo Deploy checks failed.
    pause
    exit /b 1
)

echo.
echo Deploy checks passed.
pause
