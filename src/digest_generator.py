"""Digest generator service."""

from typing import List
from datetime import datetime

from .telegram_fetcher import TelegramMessage
from .cerebras_client import CerebrasClient
from .config import Config


class DigestGenerator:
    """Generates digests from Telegram messages using Cerebras AI."""

    def __init__(self):
        self.cerebras = CerebrasClient()

    def generate_digest(
        self,
        messages: List[TelegramMessage],
        start_date: datetime,
        end_date: datetime,
    ) -> str:
        """
        Generate a digest from messages.

        Args:
            messages: List of Telegram messages
            start_date: Start date of the digest period
            end_date: End date of the digest period

        Returns:
            Generated digest text
        """
        if not messages:
            return self._generate_empty_digest(start_date, end_date)

        # Format messages for LLM
        messages_text = self._format_messages(messages)

        # Estimate tokens
        estimated_tokens = Config.estimate_tokens(messages_text)
        print(f"Estimated tokens: {estimated_tokens:,}")

        # Decide whether to use simple or map-reduce approach
        if estimated_tokens <= Config.MAX_TOKENS_PER_CHUNK:
            print("Using single-pass generation...")
            digest = self.cerebras.generate_digest(messages_text)
        else:
            print("Using map-reduce approach for large dataset...")
            chunks = self._split_into_chunks(messages_text)
            digest = self.cerebras.generate_digest_map_reduce(chunks)

        # Add header with date range
        header = self._generate_header(start_date, end_date, len(messages))

        return header + "\n\n" + digest

    def _format_messages(self, messages: List[TelegramMessage]) -> str:
        """Format messages for LLM processing."""
        formatted_blocks = []

        for msg in messages:
            formatted_blocks.append(msg.format_for_digest())

        return "\n".join(formatted_blocks)

    def _split_into_chunks(self, text: str) -> List[str]:
        """Split text into chunks based on token limit."""
        max_chars = Config.MAX_TOKENS_PER_CHUNK * Config.CHARS_PER_TOKEN
        chunks = []

        # Split by message blocks to avoid breaking messages
        blocks = text.split("\n\n")
        current_chunk = []
        current_length = 0

        for block in blocks:
            block_length = len(block) + 2  # +2 for \n\n

            if current_length + block_length > max_chars and current_chunk:
                # Save current chunk and start new one
                chunks.append("\n\n".join(current_chunk))
                current_chunk = [block]
                current_length = block_length
            else:
                current_chunk.append(block)
                current_length += block_length

        # Add remaining chunk
        if current_chunk:
            chunks.append("\n\n".join(current_chunk))

        print(f"Split into {len(chunks)} chunks")
        return chunks

    @staticmethod
    def _generate_header(start_date: datetime, end_date: datetime, message_count: int) -> str:
        """Generate digest header."""
        # Format dates
        if start_date.date() == (end_date - timedelta(days=1)).date():
            date_str = start_date.strftime("%d.%m.%Y")
        else:
            date_str = f"{start_date.strftime('%d.%m.%Y')} - {(end_date - timedelta(days=1)).strftime('%d.%m.%Y')}"

        return f"📊 ML/AI Digest — {date_str}\n{'=' * 50}\nTotal posts: {message_count}"

    @staticmethod
    def _generate_empty_digest(start_date: datetime, end_date: datetime) -> str:
        """Generate digest for when no messages found."""
        if start_date.date() == (end_date - timedelta(days=1)).date():
            date_str = start_date.strftime("%d.%m.%Y")
        else:
            date_str = f"{start_date.strftime('%d.%m.%Y')} - {(end_date - timedelta(days=1)).strftime('%d.%m.%Y')}"

        return f"""📊 ML/AI Digest — {date_str}
{'=' * 50}

❌ No messages found for the specified period.

Possible reasons:
- The specified channels contain no posts for these dates
- Check that channel names are correct (should start with @)
- Make sure you have access to the channels
"""


from datetime import timedelta
