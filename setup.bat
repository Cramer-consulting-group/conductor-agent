@echo off
REM Quick Setup Script for Conductor Agent with Google Gemini

echo ========================================
echo Conductor Agent - Quick Setup
echo ========================================
echo.

REM Check if Google API key is set
if "%GOOGLE_API_KEY%"=="" (
    echo [ERROR] Google API key not found!
    echo.
    echo Please get your API key from: https://aistudio.google.com/apikey
    echo Then run: setx GOOGLE_API_KEY "your-key-here"
    echo.
    pause
    exit /b 1
)

echo [1/4] Google API Key: Found
echo.

echo [2/4] Installing dependencies...
pip install -r requirements.txt google-generativeai
echo.

echo [3/4] Testing Google Gemini connection...
python -c "import google.generativeai as genai; genai.configure(api_key='%GOOGLE_API_KEY%'); print('✓ Connection successful!')"
echo.

echo [4/4] Ready to run!
echo.
echo ========================================
echo Next Steps:
echo ========================================
echo 1. Ingest your conversations:
echo    python ingest.py
echo.
echo 2. Start the CLI:
echo    python -m cli.interactive
echo.
echo ========================================
pause
