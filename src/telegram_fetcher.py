"""Telegram message fetcher module."""

import re
from datetime import datetime, timedelta, timezone
from typing import List, Dict, Any, Optional
from telethon import TelegramClient
from telethon.tl.types import Message

from .config import Config


class TelegramMessage:
    """Represents a processed Telegram message."""

    def __init__(
        self,
        channel_name: str,
        channel_username: str,
        date: datetime,
        text: str,
        message_id: int,
        urls: List[str],
    ):
        self.channel_name = channel_name
        self.channel_username = channel_username
        self.date = date
        self.text = text
        self.message_id = message_id
        self.urls = urls

    @property
    def message_link(self) -> str:
        """Generate a link to the message."""
        username = self.channel_username.lstrip("@")
        return f"https://t.me/{username}/{self.message_id}"

    def to_dict(self) -> Dict[str, Any]:
        """Convert to dictionary representation."""
        return {
            "channel_name": self.channel_name,
            "channel_username": self.channel_username,
            "date": self.date.isoformat(),
            "text": self.text,
            "message_id": self.message_id,
            "urls": self.urls,
            "message_link": self.message_link,
        }

    def format_for_digest(self) -> str:
        """Format message for inclusion in digest."""
        header = f"=== {self.channel_name} ({self.channel_username}) — {self.date.strftime('%Y-%m-%d %H:%M')} ===\n"
        body = self.text.strip()
        footer = f"\nLink: {self.message_link}\n"

        if self.urls:
            footer += "URLs: " + ", ".join(self.urls) + "\n"

        return header + body + footer + "\n"


class TelegramFetcher:
    """Fetches messages from Telegram channels."""

    def __init__(self):
        self.client: Optional[TelegramClient] = None

    async def __aenter__(self):
        """Async context manager entry."""
        self.client = TelegramClient(
            Config.TELEGRAM_SESSION_NAME,
            Config.TELEGRAM_API_ID,
            Config.TELEGRAM_API_HASH,
        )
        await self.client.start()
        return self

    async def __aexit__(self, exc_type, exc_val, exc_tb):
        """Async context manager exit."""
        if self.client:
            await self.client.disconnect()

    @staticmethod
    def extract_urls(text: str) -> List[str]:
        """Extract URLs from text."""
        if not text:
            return []
        return re.findall(r"https?://[^\s]+", text)

    async def fetch_messages(
        self,
        channels: List[str],
        start_date: datetime,
        end_date: Optional[datetime] = None,
    ) -> List[TelegramMessage]:
        """
        Fetch messages from specified channels within date range.

        Args:
            channels: List of channel usernames (e.g., ['@channel1', '@channel2'])
            start_date: Start date for message filtering (inclusive)
            end_date: End date for message filtering (exclusive). If None, uses start_date + 1 day

        Returns:
            List of TelegramMessage objects
        """
        if not self.client:
            raise RuntimeError("Client not initialized. Use async context manager.")

        if end_date is None:
            end_date = start_date + timedelta(days=1)

        # Ensure dates are timezone-aware
        if start_date.tzinfo is None:
            start_date = start_date.replace(tzinfo=timezone.utc)
        if end_date.tzinfo is None:
            end_date = end_date.replace(tzinfo=timezone.utc)

        all_messages: List[TelegramMessage] = []

        for channel in channels:
            print(f"Fetching messages from {channel}...")
            try:
                messages = await self._fetch_channel_messages(
                    channel, start_date, end_date
                )
                all_messages.extend(messages)
                print(f"  Found {len(messages)} messages")
            except Exception as e:
                print(f"  Error fetching from {channel}: {e}")

        # Sort by date
        all_messages.sort(key=lambda m: m.date)

        return all_messages

    async def _fetch_channel_messages(
        self, channel: str, start_date: datetime, end_date: datetime
    ) -> List[TelegramMessage]:
        """Fetch messages from a single channel."""
        messages: List[TelegramMessage] = []

        try:
            # Get channel entity
            entity = await self.client.get_entity(channel)
            channel_name = getattr(entity, "title", channel)

            # Iterate through messages
            async for message in self.client.iter_messages(
                entity, reverse=False, offset_date=end_date, limit=None
            ):
                if not isinstance(message, Message) or not message.date:
                    continue

                # Convert message date to UTC
                msg_date = message.date
                if msg_date.tzinfo is None:
                    msg_date = msg_date.replace(tzinfo=timezone.utc)
                else:
                    msg_date = msg_date.astimezone(timezone.utc)

                # Check if message is in date range
                if msg_date < start_date:
                    break  # Messages are ordered, so we can stop
                if msg_date >= end_date:
                    continue

                # Extract message content
                text = message.message or ""
                if not text.strip():
                    continue

                urls = self.extract_urls(text)

                telegram_msg = TelegramMessage(
                    channel_name=channel_name,
                    channel_username=channel,
                    date=msg_date,
                    text=text,
                    message_id=message.id,
                    urls=urls,
                )

                messages.append(telegram_msg)

        except Exception as e:
            raise RuntimeError(f"Failed to fetch messages from {channel}: {e}")

        return messages

    async def get_user_info(self) -> Dict[str, Any]:
        """Get information about the authenticated user."""
        if not self.client:
            raise RuntimeError("Client not initialized")

        me = await self.client.get_me()
        return {
            "id": me.id,
            "first_name": me.first_name,
            "last_name": me.last_name,
            "username": me.username,
            "phone": me.phone,
        }
