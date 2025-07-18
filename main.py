#!/usr/bin/env python3
"""
AI Subtitle Converter - Telegram Bot
Translates subtitle files to Persian using AI models
"""

import sys
import os
import logging

# Add src directory to Python path
sys.path.insert(0, os.path.join(os.path.dirname(__file__), 'src'))

from src.bot.telegram_bot_premium import TelegramBotPremium

def main():
    """Main entry point for the application"""
    try:
        # Create and run the premium bot
        bot = TelegramBotPremium()
        bot.run()
        
    except KeyboardInterrupt:
        print("\n🛑 Bot stopped by user")
    except Exception as e:
        print(f"❌ Error starting bot: {str(e)}")
        print("\n💡 Make sure you have:")
        print("1. Created .env file with required tokens")
        print("2. Installed all dependencies: pip install -r requirements.txt")
        print("3. Set up your Telegram bot token and OpenAI API key")
        sys.exit(1)

if __name__ == "__main__":
    main()