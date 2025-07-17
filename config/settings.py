import os
from dotenv import load_dotenv

load_dotenv()

class Settings:
    # Telegram Bot Settings
    TELEGRAM_BOT_TOKEN = os.getenv('TELEGRAM_BOT_TOKEN')
    
    # OpenAI Settings
    OPENAI_API_KEY = os.getenv('OPENAI_API_KEY')
    OPENAI_MODEL = os.getenv('OPENAI_MODEL', 'gpt-3.5-turbo')
    OPENAI_MAX_TOKENS = int(os.getenv('OPENAI_MAX_TOKENS', 4000))
    
    # Translation Settings
    TARGET_LANGUAGE = os.getenv('TARGET_LANGUAGE', 'Persian')
    SOURCE_LANGUAGE = os.getenv('SOURCE_LANGUAGE', 'auto-detect')
    
    # File Settings
    MAX_FILE_SIZE_MB = int(os.getenv('MAX_FILE_SIZE_MB', 50))
    TEMP_DIR = os.getenv('TEMP_DIR', './temp')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './output')
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @classmethod
    def validate(cls):
        """Validate required settings"""
        required_settings = [
            ('TELEGRAM_BOT_TOKEN', cls.TELEGRAM_BOT_TOKEN),
            ('OPENAI_API_KEY', cls.OPENAI_API_KEY)
        ]
        
        missing = [name for name, value in required_settings if not value]
        if missing:
            raise ValueError(f"Missing required environment variables: {', '.join(missing)}")
        
        return True

settings = Settings()