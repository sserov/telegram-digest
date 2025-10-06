"""Main entry point for Telegram Digest application."""

import argparse
import asyncio
import sys
from datetime import datetime, timedelta
from typing import List, Optional

from .config import Config
from .telegram_fetcher import TelegramFetcher
from .digest_generator import DigestGenerator
from .output_handler import OutputHandler


def parse_date(date_str: str) -> datetime:
    """Parse date string in format YYYY-MM-DD."""
    try:
        return datetime.strptime(date_str, "%Y-%m-%d")
    except ValueError:
        raise argparse.ArgumentTypeError(
            f"Invalid date format: {date_str}. Use YYYY-MM-DD"
        )


def parse_args() -> argparse.Namespace:
    """Parse command-line arguments."""
    parser = argparse.ArgumentParser(
        description="Generate ML/AI digest from Telegram channels using Cerebras AI",
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
Examples:
  # Generate digest for today using channels.yaml
  python -m src.main

  # Use specific channel group from config
  python -m src.main --group research

  # Override with specific channels
  python -m src.main --channels @ai_news @ml_research

  # Specify channels and date range
  python -m src.main --channels @ai_news @ml_research --start-date 2025-10-01 --end-date 2025-10-03

  # Use custom config file
  python -m src.main --config my_channels.yaml --group news

  # Save to file
  python -m src.main --output-file my_digest.txt

  # Send to Telegram
  python -m src.main --send-to-telegram --telegram-target @my_channel

Environment variables (set in .env file):
  TELEGRAM_API_ID, TELEGRAM_API_HASH, CEREBRAS_API_KEY (required)
  TELEGRAM_BOT_TOKEN, OUTPUT_TELEGRAM_CHANNEL (optional)
        """,
    )

    parser.add_argument(
        "--channels",
        nargs="+",
        help="Telegram channels to fetch from (e.g., @channel1 @channel2)",
    )

    parser.add_argument(
        "--config",
        type=str,
        default="channels.yaml",
        help="Path to YAML configuration file with channels (default: channels.yaml)",
    )

    parser.add_argument(
        "--group",
        type=str,
        help="Load specific channel group from config file",
    )

    parser.add_argument(
        "--start-date",
        type=parse_date,
        help="Start date (YYYY-MM-DD). Default: today",
    )

    parser.add_argument(
        "--end-date",
        type=parse_date,
        help="End date (YYYY-MM-DD), exclusive. Default: tomorrow",
    )

    parser.add_argument(
        "--output-file",
        type=str,
        help="Save digest to file (default: digest_TIMESTAMP.txt)",
    )

    parser.add_argument(
        "--send-to-telegram",
        action="store_true",
        help="Send digest to Telegram",
    )

    parser.add_argument(
        "--telegram-target",
        type=str,
        help="Telegram target for sending (e.g., @channel or user_id)",
    )

    parser.add_argument(
        "--no-console",
        action="store_true",
        help="Don't print digest to console",
    )

    return parser.parse_args()


async def main_async():
    """Main async function."""
    # Parse arguments
    args = parse_args()

    # Determine channels with priority: CLI args > YAML config > env
    channels = None
    
    if args.channels:
        # Priority 1: CLI arguments
        channels = args.channels
    else:
        # Priority 2: Try to load from YAML config
        try:
            channels = Config.get_channels_from_config(
                config_path=args.config,
                group=args.group
            )
            config_source = f"config file '{args.config}'"
            if args.group:
                config_source += f" (group: {args.group})"
            print(f"📋 Loaded channels from {config_source}")
        except FileNotFoundError:
            # Config file not found, try env default
            if Config.DEFAULT_CHANNELS:
                channels = Config.DEFAULT_CHANNELS
            else:
                pass  # Will show error below
        except Exception as e:
            print(f"⚠️  Warning: Could not load config file: {e}")
            # Try env default
            if Config.DEFAULT_CHANNELS:
                channels = Config.DEFAULT_CHANNELS
    
    if not channels:
        print("❌ Error: No channels specified.")
        print("   Options:")
        print("   1. Use --channels @channel1 @channel2")
        print("   2. Create channels.yaml (see channels.yaml.example)")
        print("   3. Set DEFAULT_CHANNELS in config")
        sys.exit(1)

    # Determine date range
    start_date = args.start_date if args.start_date else datetime.now()
    end_date = args.end_date if args.end_date else datetime.now() + timedelta(days=1)

    # Ensure start_date is at beginning of day
    start_date = start_date.replace(hour=0, minute=0, second=0, microsecond=0)
    end_date = end_date.replace(hour=0, minute=0, second=0, microsecond=0)

    print("=" * 80)
    print("🚀 Telegram Digest Generator")
    print("=" * 80)
    print(f"Channels: {', '.join(channels)}")
    print(f"Date range: {start_date.strftime('%Y-%m-%d')} to {(end_date - timedelta(days=1)).strftime('%Y-%m-%d')}")
    print(f"Model: {Config.CEREBRAS_MODEL}")
    print("=" * 80 + "\n")

    try:
        # Step 1: Fetch messages from Telegram
        print("📥 Step 1: Fetching messages from Telegram...")
        async with TelegramFetcher() as fetcher:
            # Show authenticated user
            user_info = await fetcher.get_user_info()
            print(f"Authenticated as: {user_info['first_name']} (@{user_info['username']})")

            # Check if channels list contains folder links
            if Config.has_folder_links(channels):
                print("\n🔄 Detected folder links, expanding...")
                expanded_channels = []
                for item in channels:
                    if 't.me/addlist/' in item:
                        # This is a folder link
                        print(f"   Expanding folder: {item}")
                        try:
                            folder_channels = await fetcher.get_channels_from_folder(item)
                            expanded_channels.extend(folder_channels)
                        except Exception as e:
                            print(f"   ⚠️  Failed to expand folder {item}: {e}")
                    else:
                        # Regular channel
                        expanded_channels.append(item)
                
                # Remove duplicates while preserving order
                channels = list(dict.fromkeys(expanded_channels))
                print(f"\n✅ Expanded to {len(channels)} channels: {', '.join(channels)}\n")

            messages = await fetcher.fetch_messages(channels, start_date, end_date)

            print(f"\n✅ Fetched {len(messages)} messages total\n")

            if not messages:
                print("⚠️  No messages found for the specified date range.")
                sys.exit(0)

            # Step 2: Generate digest
            print("🤖 Step 2: Generating digest with Cerebras AI...")
            generator = DigestGenerator()
            digest = generator.generate_digest(messages, start_date, end_date)

            print("✅ Digest generated\n")

            # Step 3: Output
            print("📤 Step 3: Outputting digest...")

            # Print to console (unless disabled)
            if not args.no_console:
                OutputHandler.print_to_console(digest)

            # Save to file
            if args.output_file or not args.send_to_telegram:
                # Save to file by default if not sending to Telegram
                file_path = await OutputHandler.save_to_file(digest, args.output_file)

            # Send to Telegram
            if args.send_to_telegram:
                target = args.telegram_target or Config.OUTPUT_TELEGRAM_CHANNEL
                await OutputHandler.send_to_telegram(
                    digest,
                    target=target,
                )

        print("\n" + "=" * 80)
        print("✨ Done!")
        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)

    except Exception as e:
        print(f"\n❌ Error: {e}")
        import traceback
        traceback.print_exc()
        sys.exit(1)


def main():
    """Entry point for the application."""
    try:
        asyncio.run(main_async())
    except KeyboardInterrupt:
        print("\n\n⚠️  Interrupted by user")
        sys.exit(1)


if __name__ == "__main__":
    main()
