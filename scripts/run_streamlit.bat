@echo off
setlocal

cd /d "%~dp0\.."

set "VENV_DIR=venv"
set "PYTHON_EXE=%VENV_DIR%\Scripts\python.exe"

echo ==========================================
echo Run Streamlit (Layered App)
echo ==========================================
echo.

if not exist "%PYTHON_EXE%" (
    echo Creating virtual environment...
    call :create_venv
    if errorlevel 1 goto :missing_python
)

echo Installing dependencies...
"%PYTHON_EXE%" -m pip install -r requirements.txt
if errorlevel 1 goto :pip_failed

echo.
echo Starting Streamlit app...
echo.
"%PYTHON_EXE%" -m streamlit run apps/streamlit_app/app.py
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
pause
exit /b 1

:pip_failed
echo.
echo ERROR: Failed to install dependencies.
pause
exit /b 1

:end
echo.
echo Streamlit stopped.
pause

