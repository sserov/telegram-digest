"""
Example usage of the Telegram Digest library.

This script demonstrates how to use the library programmatically.
"""

import asyncio
from datetime import datetime, timedelta

from src.config import Config
from src.telegram_fetcher import TelegramFetcher
from src.digest_generator import DigestGenerator
from src.output_handler import OutputHandler


async def example_basic_usage():
    """Basic example: fetch messages and generate digest."""
    # Define channels and date range
    channels = ["@ai_news", "@ml_research"]
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now()

    # Fetch messages
    async with TelegramFetcher() as fetcher:
        messages = await fetcher.fetch_messages(channels, start_date, end_date)

        print(f"Fetched {len(messages)} messages")

        if messages:
            # Generate digest
            generator = DigestGenerator()
            digest = generator.generate_digest(messages, start_date, end_date)

            # Output
            OutputHandler.print_to_console(digest)
            await OutputHandler.save_to_file(digest, "example_digest.txt")


async def example_with_telegram_send():
    """Example: generate and send digest to Telegram."""
    channels = ["@ai_news"]
    start_date = datetime.now() - timedelta(days=1)
    end_date = datetime.now()

    async with TelegramFetcher() as fetcher:
        messages = await fetcher.fetch_messages(channels, start_date, end_date)

        if messages:
            generator = DigestGenerator()
            digest = generator.generate_digest(messages, start_date, end_date)

            # Send to Telegram channel
            await OutputHandler.send_to_telegram(
                digest,
                target="@my_digest_channel",
                client=fetcher.client,
            )


if __name__ == "__main__":
    # Run basic example
    asyncio.run(example_basic_usage())

    # Uncomment to run Telegram send example
    # asyncio.run(example_with_telegram_send())
