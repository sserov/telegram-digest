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
    def markdown_to_html(text: str) -> str:
        """
        Convert Markdown formatting to HTML for Telegram Bot API.
        
        Converts:
        - **bold** -> <b>bold</b>
        - [text](url) -> <a href="url">text</a>
        - >quote -> <blockquote>quote</blockquote>
        
        HTML only requires escaping: & < >
        """
        import html
        
        result = []
        i = 0
        
        while i < len(text):
            # Handle **bold**
            if i < len(text) - 1 and text[i:i+2] == '**':
                close_pos = text.find('**', i + 2)
                if close_pos != -1:
                    bold_content = text[i + 2:close_pos]
                    # Escape HTML in content
                    bold_content = html.escape(bold_content)
                    result.append(f'<b>{bold_content}</b>')
                    i = close_pos + 2
                    continue
            
            # Handle [text](url)
            if text[i] == '[':
                bracket_end = text.find('](', i)
                if bracket_end != -1:
                    paren_end = text.find(')', bracket_end + 2)
                    if paren_end != -1:
                        link_text = text[i + 1:bracket_end]
                        link_url = text[bracket_end + 2:paren_end]
                        # Escape HTML in text and url
                        link_text = html.escape(link_text)
                        link_url = html.escape(link_url)
                        result.append(f'<a href="{link_url}">{link_text}</a>')
                        i = paren_end + 1
                        continue
            
            # Handle >quote at start of line
            if text[i] == '>' and (i == 0 or text[i - 1] == '\n'):
                # Find end of line
                line_end = text.find('\n', i + 1)
                if line_end == -1:
                    line_end = len(text)
                
                quote_content = text[i + 1:line_end].strip()
                quote_content = html.escape(quote_content)
                result.append(f'<blockquote>{quote_content}</blockquote>')
                i = line_end
                continue
            
            # Regular character - escape HTML special chars
            if text[i] in '&<>':
                result.append(html.escape(text[i]))
            else:
                result.append(text[i])
            
            i += 1
        
        return ''.join(result)

    @staticmethod
    def send_via_bot_api(digest: str, target: str) -> bool:  # NOT async
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
        
        # Convert Markdown to HTML
        html_text = OutputHandler.markdown_to_html(digest)
        
        payload = {
            "chat_id": target,
            "text": html_text,
            "parse_mode": "HTML",
            "disable_web_page_preview": True  # Disable link previews
        }
        
        try:
            response = requests.post(url, json=payload, timeout=30)
            
            result = response.json()
            if result.get("ok"):
                print(f"✅ Digest sent to {target} via Bot API")
                return True
            else:
                error_desc = result.get('description', 'Unknown error')
                print(f"❌ Bot API error: {error_desc}")
                # Print first 500 chars of HTML text for debugging
                print(f"Debug: First 500 chars of HTML text:")
                print(html_text[:500])
                print(f"Debug: Last 200 chars:")
                print(html_text[-200:])
                return False
                
        except requests.exceptions.HTTPError as e:
            print(f"❌ HTTP Error: {e}")
            if hasattr(e, 'response') and e.response is not None:
                print(f"Response: {e.response.text[:500]}")
            return False
        except requests.exceptions.RequestException as e:
            print(f"❌ Failed to send via Bot API: {e}")
            return False
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
    ) -> bool:
        """
        Send digest to Telegram channel or chat via Bot API.

        Args:
            digest: Digest text to send
            target: Target channel/chat (e.g., '@channel' or user_id). If None, uses config.

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
            return OutputHandler._send_long_message_bot_api_sync(digest, target)

        try:
            # Use Bot API (HTML formatting)
            return OutputHandler.send_via_bot_api(digest, target)

        except Exception as e:
            print(f"❌ Failed to send to Telegram: {e}")
            return False

    @staticmethod
    def _send_long_message_bot_api_sync(digest: str, target: str) -> bool:  # NOT async
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
            # Add part header with bold formatting
            part_with_header = f"**[Part {i}/{len(parts)}]**\n\n{part}"
            
            print(f"📤 Sending part {i}/{len(parts)} ({len(part_with_header)} chars)...")
            result = OutputHandler.send_via_bot_api(part_with_header, target)  # NOT await
            
            if not result:
                success = False
                print(f"❌ Failed to send part {i}/{len(parts)}")
                print(f"   Part length: {len(part_with_header)} chars")
                print(f"   First 200 chars of part: {part_with_header[:200]}")
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
