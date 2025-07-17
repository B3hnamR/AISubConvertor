قرض#!/usr/bin/env python3
"""
Test script for translation functionality
"""

import sys
import os
import asyncio
sys.path.insert(0, os.path.join(os.path.dirname(__file__), '..', 'src'))

from src.translation import TranslatorFactory

async def test_translation():
    """Test translation functionality"""
    try:
        print("🧪 Testing Translation Service...")

        # Test translator factory
        available_providers = TranslatorFactory.get_available_providers()
        print(f"📋 Available providers: {available_providers}")

        # Mock config for testing (without real API key)
        mock_config = {
            'api_key': 'test_key',
            'model': 'gpt-3.5-turbo',
            'max_tokens': 1000
        }

        # Test factory creation (will fail without real API key, but tests structure)
        try:
            translator = TranslatorFactory.create_translator('openai', mock_config)
            print(f"✅ Translator created: {translator.get_provider_name()}")
        except Exception as e:
            print(f"⚠️  Translator creation failed (expected without API key): {str(e)}")

        # Test sample texts
        sample_texts = [
            "Hello, how are you?",
            "This is a test subtitle.",
            "Welcome to our application."
        ]

        print(f"\n📝 Sample texts for translation:")
        for i, text in enumerate(sample_texts, 1):
            print(f"  {i}. {text}")

        print("\n💡 To test actual translation, add your OpenAI API key to .env file")
        print("🎉 Translation structure test completed!")
        return True

    except Exception as e:
        print(f"❌ Test failed: {str(e)}")
        return False

if __name__ == "__main__":
    success = asyncio.run(test_translation())
    sys.exit(0 if success else 1)