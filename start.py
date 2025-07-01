#!/usr/bin/env python3
"""
Telegram Questionnaire Bot Startup Script
"""

import sys
import os
from pathlib import Path

# Add current directory to path
sys.path.insert(0, str(Path(__file__).parent))

def check_requirements():
    """Check if all required packages are installed"""
    try:
        import telegram
        import pandas
        import openpyxl
        return True
    except ImportError as e:
        print(f"❌ Missing required package: {e}")
        print("Please install requirements: pip install -r requirements.txt")
        return False

def check_config():
    """Check if configuration is valid"""
    try:
        from config import Config
        
        if not Config.validate_config():
            print("❌ Invalid configuration!")
            print("Please check your BOT_TOKEN and ADMIN_USER_IDS in config.py file")
            return False
        
        print("✅ Configuration is valid")
        return True
        
    except Exception as e:
        print(f"❌ Configuration error: {e}")
        return False

def main():
    """Main startup function"""
    print("🤖 Starting Telegram Questionnaire Bot...")
    print("=" * 50)
    
    # Check requirements
    if not check_requirements():
        sys.exit(1)
    
    # Check configuration
    if not check_config():
        sys.exit(1)
    
    # Start the bot
    try:
        from bot import main as bot_main
        bot_main()
    except KeyboardInterrupt:
        print("\n👋 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {e}")
        sys.exit(1)

if __name__ == "__main__":
    main() 