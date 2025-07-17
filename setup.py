یاز#!/usr/bin/env python3
"""
Setup script for AI Subtitle Converter
"""

import os
import sys
from pathlib import Path

def create_directories():
    """Create necessary directories"""
    directories = ['temp', 'output', 'logs']

    for directory in directories:
        Path(directory).mkdir(exist_ok=True)
        print(f"✅ Created directory: {directory}")

def setup_environment():
    """Setup environment file"""
    env_example = ".env.example"
    env_file = ".env"

    if not os.path.exists(env_file):
        if os.path.exists(env_example):
            # Copy example to .env
            with open(env_example, 'r') as f:
                content = f.read()

            with open(env_file, 'w') as f:
                f.write(content)

            print(f"✅ Created {env_file} from {env_example}")
            print(f"⚠️  Please edit {env_file} and add your API keys!")
        else:
            print(f"❌ {env_example} not found")
    else:
        print(f"✅ {env_file} already exists")

def install_dependencies():
    """Install Python dependencies"""
    try:
        import subprocess
        result = subprocess.run([sys.executable, '-m', 'pip', 'install', '-r', 'requirements.txt'],
                              capture_output=True, text=True)

        if result.returncode == 0:
            print("✅ Dependencies installed successfully")
        else:
            print(f"❌ Failed to install dependencies: {result.stderr}")
            return False
    except Exception as e:
        print(f"❌ Error installing dependencies: {str(e)}")
        return False

    return True

def main():
    """Main setup function"""
    print("🚀 Setting up AI Subtitle Converter...")
    print("=" * 50)

    # Create directories
    create_directories()

    # Setup environment
    setup_environment()

    # Install dependencies
    if install_dependencies():
        print("\n" + "=" * 50)
        print("✅ Setup completed successfully!")
        print("\n📝 Next steps:")
        print("1. Edit .env file and add your API keys:")
        print("   - TELEGRAM_BOT_TOKEN (from @BotFather)")
        print("   - OPENAI_API_KEY (from OpenAI)")
        print("2. Run the bot: python main.py")
        print("\n🤖 Enjoy your subtitle translation bot!")
    else:
        print("\n❌ Setup failed. Please install dependencies manually:")
        print("pip install -r requirements.txt")

if __name__ == "__main__":
    main()