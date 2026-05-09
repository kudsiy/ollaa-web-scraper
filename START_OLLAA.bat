@echo off
setlocal enabledelayedexpansion

echo ========================================
echo   OLLAA Web Scraper - Starting Up...
echo ========================================

:: Database Configuration
set OLLAADB_HOST=localhost
set OLLAADB_PORT=5432
set OLLAADB_NAME=ollaa
set OLLAADB_USER=postgres
set OLLAADB_PASSWORD=4624

:: Handle Amharic/UTF-8 characters in terminal
set PYTHONUTF8=1
chcp 65001 > nul

cd /d %~dp0

:: Check for Virtual Environment
if not exist .venv (
    echo Creating virtual environment...
    python -m venv .venv
    if errorlevel 1 (
        echo ERROR: Failed to create virtual environment. 
        echo Falling back to system python with --user flag...
        goto :SYSTEM_PYTHON
    )
)

:: Activate Virtual Environment
call .venv\Scripts\activate
if errorlevel 1 (
    echo ERROR: Failed to activate virtual environment.
    goto :SYSTEM_PYTHON
)

echo.
echo Checking/Installing dependencies...
python -m pip install -r requirements.txt --no-cache-dir
if errorlevel 1 (
    echo WARNING: Dependency installation had some issues. Trying to continue...
)

:: Ensure Playwright browsers are installed
echo.
echo Checking browser dependencies...
python -m playwright install chromium
if errorlevel 1 (
    echo WARNING: Playwright browser installation failed. Some scrapers may not work.
)

goto :RUN_SCRAPER

:SYSTEM_PYTHON
echo.
echo Installing dependencies to user space...
python -m pip install -r requirements.txt --user --no-cache-dir
if errorlevel 1 (
    echo ERROR: Dependency installation failed even with --user flag.
    echo Please check your internet connection and permissions.
)

:RUN_SCRAPER
echo.
echo Starting scraper...
echo.

:: Ask if user wants diagnostic mode if DB might be down
echo Options:
echo 1. Start Normal (Requires Postgres)
echo 2. Start Diagnostic (Mock Database, testing only)
echo.
set /p choice="Choose an option [1]: "

if "%choice%"=="2" (
    echo Running in DIAGNOSTIC mode...
    python scheduler.py --diagnostic %*
) else (
    python scheduler.py %*
)

if errorlevel 1 (
    echo.
    echo Scraper crashed or failed to start.
    echo If it was a database error, try running in DIAGNOSTIC mode.
)

pause
