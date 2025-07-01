@echo off
REM Telegram Questionnaire Bot Startup Script for Windows

echo 🤖 Starting Telegram Questionnaire Bot...
echo ================================================

REM Check if config.py is properly configured
echo 📋 Please make sure you have configured your BOT_TOKEN and ADMIN_USER_IDS in config.py

REM Check if Python is available
python --version >nul 2>&1
if errorlevel 1 (
    echo ❌ Python is not installed or not in PATH
    pause
    exit /b 1
)

REM Install requirements
echo 📦 Installing requirements...
python -m pip install -r requirements.txt

REM Start the bot
echo 🚀 Starting bot...
python start.py

pause 