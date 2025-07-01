#!/bin/bash

# Telegram Questionnaire Bot Startup Script for Linux/Mac

echo "🤖 Starting Telegram Questionnaire Bot..."
echo "================================================"

# Check if config.py is properly configured
echo "📋 Please make sure you have configured your BOT_TOKEN and ADMIN_USER_IDS in config.py"

# Check if Python is available
if ! command -v python3 &> /dev/null; then
    echo "❌ Python 3 is not installed"
    exit 1
fi

# Check if pip is available
if ! command -v pip &> /dev/null && ! command -v pip3 &> /dev/null; then
    echo "❌ pip is not installed"
    exit 1
fi

# Install requirements if needed
echo "📦 Checking requirements..."
python3 -m pip install -r requirements.txt

# Start the bot
echo "🚀 Starting bot..."
python3 start.py 