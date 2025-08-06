@echo off
echo ========================================
echo User Activity and License Analyzer (Basic)
echo ========================================
echo.

REM Check if virtual environment Python is available
if exist "venv\Scripts\python.exe" (
    set PYTHON_CMD=venv\Scripts\python.exe
) else (
    REM Try system Python
    python --version >nul 2>&1
    if errorlevel 1 (
        echo ERROR: Python is not installed or not in PATH
        echo Please install Python 3.8 or higher
        echo Or ensure the virtual environment is set up correctly
        pause
        exit /b 1
    ) else (
        set PYTHON_CMD=python
    )
)

REM Check if log file path is provided
if "%~1"=="" (
    echo Usage: run_activity_analyzer.bat [log_file_path] [options]
    echo.
    echo Examples:
    echo   run_activity_analyzer.bat "license logs/"
    echo   run_activity_analyzer.bat "license logs/*.log" --output-format summary
    echo   run_activity_analyzer.bat "license logs/" --output-format json --limit 20
    echo.
    echo Available options:
    echo   --output-format summary  Generate comprehensive summary report
    echo   --output-format json     Output as JSON format
    echo   --output-format csv      Output as CSV format
    echo   --limit 20              Limit results to top 20 users
    echo   --sort-by total_login_time  Sort by total login time
    echo   --filter-user admin      Filter by user ID
    echo   --top-percentile 0.1     Analyze top 0.1%% users
    echo.
    pause
    exit /b 1
)

REM Run the analyzer (no dependencies needed!)
echo.
echo Starting analysis...
echo ========================================
%PYTHON_CMD% user_activity_analyzer_basic.py --log-file "%~1" %2 %3 %4 %5 %6 %7 %8 %9

echo.
echo Analysis complete!
echo.
pause 