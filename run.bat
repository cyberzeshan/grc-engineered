@echo off
REM Change to the directory containing this script, regardless of where it was launched from
cd /d "%~dp0"

REM Sync all dependencies from uv.lock (creates .venv if it doesn't exist)
uv sync --system-certs
if %errorlevel% neq 0 (
    echo.
    echo ERROR: dependency installation failed. Is uv installed?
    echo Install uv from: https://docs.astral.sh/uv/getting-started/installation/
    pause
    exit /b 1
)

REM Launch the Streamlit dashboard inside the project venv
uv run streamlit run ui/app.py
