@echo off
echo ============================================================
echo Mobileye Business IS Tools Web Interface
echo ============================================================
echo.
echo Starting web server...
echo.
echo The web application will be available at:
echo http://localhost:5000
echo.
echo Press Ctrl+C to stop the server
echo ============================================================
echo.

cd /d "%~dp0"
call venv\Scripts\activate.bat
python app.py

pause 