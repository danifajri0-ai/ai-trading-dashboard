@echo off
setlocal

cd /d "%~dp0"

set "VENV_DIR=venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"
set "STREAMLIT_EXE=%VENV_DIR%\Scripts\streamlit.exe"

echo ==========================================
echo AI Trading Dashboard Launcher
echo ==========================================
echo.

if exist "%PYTHON_EXE%" (
    "%PYTHON_EXE%" -c "import sys; print(sys.version)" >nul 2>&1
    if errorlevel 1 (
        echo Existing venv is broken. Recreating venv...
        rmdir /s /q "%VENV_DIR%" >nul 2>&1
    )
)

if not exist "%PYTHON_EXE%" (
    echo Creating virtual environment...
    call :create_venv
    if errorlevel 1 goto :missing_python
)

echo Installing dependencies...
"%PYTHON_EXE%" -m pip install --upgrade pip
if errorlevel 1 goto :pip_failed

"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_failed

echo Verifying dependencies...
"%PYTHON_EXE%" -c "import streamlit, yfinance, pandas, plotly, ta; import _cffi_backend" >nul 2>&1
if errorlevel 1 (
    echo Dependencies look incomplete. Reinstalling cleanly...
    "%PYTHON_EXE%" -m pip install --upgrade --force-reinstall -r requirements.txt
    if errorlevel 1 goto :pip_failed
)

echo.
echo Starting Streamlit dashboard...
echo Browser should open automatically. If not, copy the local URL shown below.
echo.
"%PYTHON_EXE%" -m streamlit run app.py
goto :end

:create_venv
py -3.11 -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

py -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

python -m venv "%VENV_DIR%" >nul 2>&1
if not errorlevel 1 exit /b 0

exit /b 1

:missing_python
echo.
echo ERROR: Python is not installed or not available in PATH.
echo Install Python 3.11 or newer, then run this file again.
echo Download: https://www.python.org/downloads/
pause
exit /b 1

:pip_failed
echo.
echo ERROR: Failed to install dependencies.
echo Check your internet connection, then run this file again.
pause
exit /b 1

:end
echo.
echo Dashboard stopped.
pause
