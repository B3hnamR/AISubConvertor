#!/usr/bin/env python3
"""
AI Subtitle Converter - Telegram Bot
Translates subtitle files to Persian using AI models
"""

import sys
import os
import logging
from pathlib import Path

# Add project root to Python path for proper imports
project_root = Path(__file__).parent
sys.path.insert(0, str(project_root))

# Initialize logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
)

from src.bot import TelegramBotPremium
from src.utils import get_error_handler, handle_errors, get_backup_manager
from config import settings, get_dynamic_settings

@handle_errors(reraise=True)
def initialize_system():
    """Initialize system components"""
    try:
        # Validate configuration
        settings.validate()
        
        # Initialize dynamic settings
        dynamic_settings = get_dynamic_settings()
        logging.info("Dynamic settings initialized")
        
        # Initialize backup manager
        backup_manager = get_backup_manager(settings.DATABASE_PATH)
        logging.info("Backup manager initialized")
        
        # Create necessary directories
        os.makedirs(settings.TEMP_DIR, exist_ok=True)
        os.makedirs(settings.OUTPUT_DIR, exist_ok=True)
        logging.info("Required directories created")
        
        return True
        
    except Exception as e:
        logging.error(f"System initialization failed: {e}")
        raise

def main():
    """Main entry point for the application"""
    try:
        # Initialize system
        initialize_system()
        
        # Create and run the premium bot
        logging.info("Starting AI Subtitle Converter Bot...")
        bot = TelegramBotPremium()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
        logging.info("Bot stopped by user")
    except Exception as e:
        error_handler = get_error_handler()
        error_handler.log_error(e, {'component': 'main'})
        
        print(f"❌ Error starting bot: {str(e)}")
        print("\n💡 Make sure you have:")
        print("1. Created .env file with required tokens")
        print("2. Installed all dependencies: pip install -r requirements.txt")
        print("3. Set up your Telegram bot token and OpenAI API key")
        sys.exit(1)

if __name__ == "__main__":
    main()