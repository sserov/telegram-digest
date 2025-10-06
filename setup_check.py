#!/usr/bin/env python3
"""
Setup script to help configure the Telegram Digest application.
Run this after installing dependencies to check your configuration.
"""

import os
import sys
from pathlib import Path


def check_env_file():
    """Check if .env file exists."""
    env_path = Path(".env")
    if not env_path.exists():
        print("❌ .env file not found")
        print("   Creating from template...")
        example_path = Path(".env.example")
        if example_path.exists():
            import shutil
            shutil.copy(example_path, env_path)
            print("✅ Created .env file from .env.example")
            print("   Please edit .env and add your credentials")
            return False
        else:
            print("❌ .env.example not found")
            return False
    else:
        print("✅ .env file exists")
        return True


def check_env_variables():
    """Check if required environment variables are set."""
    from dotenv import load_dotenv
    load_dotenv()

    required = {
        "TELEGRAM_API_ID": os.getenv("TELEGRAM_API_ID"),
        "TELEGRAM_API_HASH": os.getenv("TELEGRAM_API_HASH"),
        "CEREBRAS_API_KEY": os.getenv("CEREBRAS_API_KEY"),
    }

    all_set = True
    for key, value in required.items():
        if not value or value.startswith("your_"):
            print(f"❌ {key} not set properly in .env")
            all_set = False
        else:
            masked = value[:8] + "..." if len(value) > 8 else "***"
            print(f"✅ {key} = {masked}")

    return all_set


def check_dependencies():
    """Check if required packages are installed."""
    packages = ["telethon", "dotenv", "cerebras"]

    all_installed = True
    for package in packages:
        try:
            __import__(package.replace("-", "_"))
            print(f"✅ {package} installed")
        except ImportError:
            print(f"❌ {package} not installed")
            all_installed = False

    return all_installed


def provide_help():
    """Provide helpful next steps."""
    print("\n" + "=" * 60)
    print("NEXT STEPS")
    print("=" * 60)

    print("\n1. Get Telegram API credentials:")
    print("   https://my.telegram.org/apps")

    print("\n2. Get Cerebras API key:")
    print("   https://cloud.cerebras.ai/")

    print("\n3. Update .env file with your credentials")

    print("\n4. Run your first digest:")
    print("   python -m src.main --channels @ai_news --start-date 2025-10-04")

    print("\n5. Check QUICKSTART.md for detailed instructions")


def main():
    """Main setup check."""
    print("=" * 60)
    print("Telegram Digest - Setup Check")
    print("=" * 60 + "\n")

    # Check dependencies
    print("Checking dependencies...")
    deps_ok = check_dependencies()
    print()

    if not deps_ok:
        print("⚠️  Install dependencies first:")
        print("   pip install -r requirements.txt")
        sys.exit(1)

    # Check .env file
    print("Checking configuration...")
    env_exists = check_env_file()
    print()

    if not env_exists:
        provide_help()
        sys.exit(1)

    # Check environment variables
    vars_ok = check_env_variables()
    print()

    if not vars_ok:
        print("⚠️  Please update .env file with your credentials")
        provide_help()
        sys.exit(1)

    # All good
    print("=" * 60)
    print("✅ Configuration looks good!")
    print("=" * 60)
    print("\nYou're ready to generate your first digest!")
    print("\nExample command:")
    print("  python -m src.main --channels @ai_news --start-date 2025-10-04")
    print("\nFor more examples, see QUICKSTART.md")


if __name__ == "__main__":
    main()
