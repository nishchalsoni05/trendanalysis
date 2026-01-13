@echo off
REM Quick start script for Aadhaar Sanket Dashboard
REM Just run: start.bat

echo ============================================
echo Starting Aadhaar Sanket Dashboard...
echo ============================================
echo.

REM Check if dependencies are installed
python -c "import streamlit" 2>nul
if errorlevel 1 (
    echo Installing dependencies...
    pip install -r requirements.txt
    echo.
)

echo Starting Streamlit dashboard...
echo.
echo Dashboard will open in your browser automatically.
echo Press Ctrl+C techo Starting Aadhaar Sanket Dashboard...
echo.

streamlit run frontend/1_Overview.py
pause
