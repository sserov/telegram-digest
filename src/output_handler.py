"""Output handlers for digest results."""

import os
import re
import requests
from pathlib import Path
from datetime import datetime
from typing import Optional

from telethon import TelegramClient
from telethon.tl.custom import Message

from .config import Config


class OutputHandler:
    """Handles output of generated digests."""

    @staticmethod
    def escape_markdown_v2(text: str) -> str:
        """
        Escape special characters for MarkdownV2 format.
        
        In MarkdownV2, these characters must be escaped: _ * [ ] ( ) ~ ` > # + - = | { } . !
        But we need to preserve formatting characters that are already part of markdown syntax.
        """
        # Characters that need escaping in MarkdownV2
        # We'll be smart about it - don't escape if it's part of valid markdown
        escape_chars = r'_*[]()~`>#+-=|{}.!'
        
        # This is a simplified approach - escape all special chars except in markdown constructs
        # For production, you might want more sophisticated parsing
        result = []
        i = 0
        while i < len(text):
            char = text[i]
            
            # Check if we're in a markdown bold (**text**)
            if char == '*' and i + 1 < len(text) and text[i + 1] == '*':
                # This is bold markdown, keep it
                result.append('**')
                i += 2
                continue
            
            # Check if we're in a link [text](url)
            if char == '[':
                # Find the closing ] and following (url)
                close_bracket = text.find(']', i)
                if close_bracket != -1 and close_bracket + 1 < len(text) and text[close_bracket + 1] == '(':
                    close_paren = text.find(')', close_bracket)
                    if close_paren != -1:
                        # This is a valid link, keep it as is
                        result.append(text[i:close_paren + 1])
                        i = close_paren + 1
                        continue
            
            # Check if we're at the start of a line with > (quote)
            if char == '>' and (i == 0 or text[i - 1] == '\n'):
                # This is a quote marker, keep it
                result.append('>')
                i += 1
                continue
            
            # Check if this is a special character that needs escaping
            if char in escape_chars:
                result.append('\\' + char)
            else:
                result.append(char)
            
            i += 1
        
        return ''.join(result)

    @staticmethod
    async def send_via_bot_api(digest: str, target: str) -> bool:
        """
        Send message via Telegram Bot API (recommended for MarkdownV2).
        
        Args:
            digest: Digest text to send
            target: Target channel (@channel_name) or chat_id
            
        Returns:
            True if sent successfully, False otherwise
        """
        if not Config.TELEGRAM_BOT_TOKEN:
            print("❌ TELEGRAM_BOT_TOKEN not configured")
            return False
        
        url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"
        
        # Escape text for MarkdownV2
        escaped_text = OutputHandler.escape_markdown_v2(digest)
        
        payload = {
            "chat_id": target,
            "text": escaped_text,
            "parse_mode": "MarkdownV2",
            "disable_web_page_preview": False  # Allow link previews
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            response.raise_for_status()
            
            result = response.json()
            if result.get("ok"):
                print(f"✅ Digest sent to {target} via Bot API")
                return True
            else:
                print(f"❌ Bot API error: {result.get('description', 'Unknown error')}")
                return False
                
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send via Bot API: {e}")
            return False

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
        use_bot: bool = True,  # Changed default to True - prefer Bot API
        client: Optional[TelegramClient] = None,
    ) -> bool:
        """
        Send digest to Telegram channel or chat.

        Args:
            digest: Digest text to send
            target: Target channel/chat (e.g., '@channel' or user_id). If None, uses config.
            use_bot: Whether to use Bot API (recommended, default=True)
            client: Existing TelegramClient (for user session). Ignored if use_bot=True.

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
            print("   Splitting into multiple messages...")
            return await OutputHandler._send_long_message_bot_api(digest, target)

        try:
            if use_bot:
                # Use Bot API (recommended for MarkdownV2)
                return await OutputHandler.send_via_bot_api(digest, target)
            else:
                # Fallback to Telethon user client
                return await OutputHandler._send_via_user_client(digest, target, client)
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
            await bot_client.send_message(target, digest, parse_mode='MarkdownV2')
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
            await client.send_message(target, digest, parse_mode='MarkdownV2')
            print(f"✅ Digest sent to {target}")
            return True

        except Exception as e:
            print(f"❌ Send error: {e}")
            return False

        finally:
            if should_disconnect:
                await client.disconnect()

    @staticmethod
    async def _send_long_message_bot_api(digest: str, target: str) -> bool:
        """
        Handle sending of long messages by splitting (Bot API version).
        
        Args:
            digest: Digest text to send
            target: Target channel or chat
            
        Returns:
            True if all parts sent successfully
        """
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

        print(f"📤 Sending digest in {len(parts)} parts via Bot API...")

        success = True
        for i, part in enumerate(parts, 1):
            part_with_header = f"**\\[Part {i}/{len(parts)}\\]**\n\n{part}"
            
            result = await OutputHandler.send_via_bot_api(part_with_header, target)
            
            if not result:
                success = False
                print(f"❌ Failed to send part {i}/{len(parts)}")
                break

            print(f"✅ Sent part {i}/{len(parts)}")

        return success

    @staticmethod
    async def _send_long_message(
        digest: str,
        target: str,
        use_bot: bool = False,
        client: Optional[TelegramClient] = None,
    ) -> bool:
        """Handle sending of long messages by splitting (legacy Telethon version)."""
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
