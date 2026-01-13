@echo off
setlocal
REM Quick start script for Aadhaar Sanket Dashboard

echo ============================================
echo Starting Aadhaar Sanket Dashboard
echo ============================================
echo.

REM --- 1. Check for Python ---
echo [CHECK] Checking Python version...
python --version
if %errorlevel% neq 0 goto :python_error

REM --- 2. Check Virtual Environment ---
if exist ".venv" goto :activate_venv

echo [INFO] Virtual environment not found. Creating one...
python -m venv .venv
if %errorlevel% neq 0 goto :venv_create_error
echo [SUCCESS] Virtual environment created.

:activate_venv
echo [INFO] Activating virtual environment...
if not exist ".venv\Scripts\activate.bat" goto :venv_script_error
call ".venv\Scripts\activate.bat"

REM --- 3. Install Dependencies ---
echo [INFO] Checking dependencies...
python -m pip install --upgrade pip
pip install -r requirements.txt
if %errorlevel% neq 0 goto :install_error

REM --- 4. Run Application ---
echo.
echo [SUCCESS] Environment ready! Launching dashboard...
echo.
echo Press Ctrl+C to stop.
echo.

streamlit run frontend/1_Overview.py
if %errorlevel% neq 0 goto :app_error

goto :end

REM --- Error Handlers ---

:python_error
echo.
echo [ERROR] Python is not installed or not in your PATH.
echo Please install Python 3.10+ from python.org and try again.
pause
exit /b 1

:venv_create_error
echo.
echo [ERROR] Failed to create virtual environment.
echo Please check your permissions or try running as Administrator.
pause
exit /b 1

:venv_script_error
echo.
echo [ERROR] Virtual environment seems corrupted (missing activate.bat).
echo Please delete the '.venv' folder manually and run this script again.
pause
exit /b 1

:install_error
echo.
echo [ERROR] Failed to install dependencies.
echo Check your internet connection or 'requirements.txt'.
pause
exit /b 1

:app_error
echo.
echo [ERROR] Application stopped unexpectedly.
pause
exit /b 1

:end
endlocal
