"""Output handlers for digest results."""

import os
from pathlib import Path
from datetime import datetime
from typing import Optional

from telethon import TelegramClient
from telethon.tl.custom import Message

from .config import Config


class OutputHandler:
    """Handles output of generated digests."""

    @staticmethod
    async def save_to_file(digest: str, file_path: Optional[str] = None) -> str:
        """
        Save digest to a file.

        Args:
            digest: Digest text to save
            file_path: Optional custom file path. If None, generates default name.

        Returns:
            Path to saved file
        """
        if file_path is None:
            # Generate default filename with timestamp
            timestamp = datetime.now().strftime("%Y-%m-%d_%H-%M-%S")
            file_path = f"digest_{timestamp}.txt"

        # Create parent directories if needed
        path = Path(file_path)
        path.parent.mkdir(parents=True, exist_ok=True)

        # Save digest
        with open(path, "w", encoding="utf-8") as f:
            f.write(digest)

        abs_path = path.absolute()
        print(f"\n✅ Digest saved to: {abs_path}")

        return str(abs_path)

    @staticmethod
    async def send_to_telegram(
        digest: str,
        target: Optional[str] = None,
        use_bot: bool = False,
        client: Optional[TelegramClient] = None,
    ) -> bool:
        """
        Send digest to Telegram channel or chat.

        Args:
            digest: Digest text to send
            target: Target channel/chat (e.g., '@channel' or user_id). If None, uses config.
            use_bot: Whether to use bot token instead of user client
            client: Existing TelegramClient (for user session). If None and use_bot=False, creates new.

        Returns:
            True if sent successfully, False otherwise
        """
        if target is None:
            target = Config.OUTPUT_TELEGRAM_CHANNEL

        if not target:
            print("❌ No Telegram target specified")
            return False

        # Check digest length (Telegram has 4096 character limit per message)
        if len(digest) > 4000:
            print("⚠️  Digest is too long for a single Telegram message.")
            print("   Splitting into multiple messages or truncating...")
            return await OutputHandler._send_long_message(digest, target, use_bot, client)

        try:
            if use_bot:
                return await OutputHandler._send_via_bot(digest, target)
            else:
                return await OutputHandler._send_via_user_client(digest, target, client)

        except Exception as e:
            print(f"❌ Failed to send to Telegram: {e}")
            return False

    @staticmethod
    async def _send_via_bot(digest: str, target: str) -> bool:
        """Send message via bot."""
        if not Config.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not configured")
            return False

        bot_client = TelegramClient(
            "bot_session", Config.TELEGRAM_API_ID, Config.TELEGRAM_API_HASH
        )

        try:
            await bot_client.start(bot_token=Config.TELEGRAM_BOT_TOKEN)
            await bot_client.send_message(target, digest)
            print(f"✅ Digest sent to {target} via bot")
            return True

        except Exception as e:
            print(f"❌ Bot send error: {e}")
            return False

        finally:
            await bot_client.disconnect()

    @staticmethod
    async def _send_via_user_client(
        digest: str, target: str, client: Optional[TelegramClient] = None
    ) -> bool:
        """Send message via user client."""
        should_disconnect = False

        if client is None:
            # Create new client
            client = TelegramClient(
                Config.TELEGRAM_SESSION_NAME,
                Config.TELEGRAM_API_ID,
                Config.TELEGRAM_API_HASH,
            )
            await client.start()
            should_disconnect = True

        try:
            await client.send_message(target, digest)
            print(f"✅ Digest sent to {target}")
            return True

        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

        finally:
            if should_disconnect:
                await client.disconnect()

    @staticmethod
    async def _send_long_message(
        digest: str,
        target: str,
        use_bot: bool = False,
        client: Optional[TelegramClient] = None,
    ) -> bool:
        """Handle sending of long messages by splitting."""
        # Split by sections/paragraphs to avoid breaking mid-sentence
        max_length = 4000
        parts = []

        # Try to split on section boundaries first
        sections = digest.split("\n\n")
        current_part = ""

        for section in sections:
            if len(current_part) + len(section) + 2 <= max_length:
                current_part += section + "\n\n"
            else:
                if current_part:
                    parts.append(current_part.strip())
                current_part = section + "\n\n"

        if current_part:
            parts.append(current_part.strip())

        print(f"📤 Sending digest in {len(parts)} parts...")

        success = True
        for i, part in enumerate(parts, 1):
            part_with_header = f"[Part {i}/{len(parts)}]\n\n{part}"

            if use_bot:
                result = await OutputHandler._send_via_bot(part_with_header, target)
            else:
                result = await OutputHandler._send_via_user_client(
                    part_with_header, target, client
                )

            if not result:
                success = False
                print(f"❌ Failed to send part {i}/{len(parts)}")
                break

            print(f"✅ Sent part {i}/{len(parts)}")

        return success

    @staticmethod
    def print_to_console(digest: str) -> None:
        """Print digest to console."""
        print("\n" + "=" * 80)
        print("GENERATED DIGEST")
        print("=" * 80 + "\n")
        print(digest)
        print("\n" + "=" * 80 + "\n")
