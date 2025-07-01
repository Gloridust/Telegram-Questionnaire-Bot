class Config:
    # Bot configuration
    # Get your bot token from @BotFather on Telegram
    BOT_TOKEN = '123456789:ABCdefGHIjklMNOpqrsTUVwxyz-example'
    
    # Admin configuration (list of user IDs)
    # Get your user ID from @userinfobot on Telegram
    ADMIN_USER_IDS = [
        123456789,    # Your user ID
        987654321,    # Another admin's user ID (optional)
    ]
    
    # Database configuration
    DATABASE_PATH = 'questionnaire_bot.db'
    
    # Other settings
    MAX_QUESTIONS_PER_QUESTIONNAIRE = 20
    MAX_OPTIONS_PER_QUESTION = 10
    
    @classmethod
    def is_admin(cls, user_id: int) -> bool:
        """Check if user is admin"""
        return user_id in cls.ADMIN_USER_IDS
    
    @classmethod
    def validate_config(cls) -> bool:
        """Validate configuration"""
        if not cls.BOT_TOKEN or cls.BOT_TOKEN == 'YOUR_BOT_TOKEN_HERE':
            print("❌ Please set your BOT_TOKEN in config.py")
            print("   Get your bot token from @BotFather on Telegram")
            return False
        if not cls.ADMIN_USER_IDS:
            print("❌ Please add at least one ADMIN_USER_ID in config.py")
            print("   Get your user ID from @userinfobot on Telegram")
            return False
        return True 