"""Cerebras AI client for digest generation."""

from typing import List, Dict, Any, Optional
from cerebras.cloud.sdk import Cerebras

from .config import Config


class CerebrasClient:
    """Client for interacting with Cerebras AI API."""

    def __init__(self):
        """Initialize Cerebras client."""
        self.client = Cerebras(api_key=Config.CEREBRAS_API_KEY)
        self.model = Config.CEREBRAS_MODEL
        self.temperature = Config.TEMPERATURE
        self.max_tokens = Config.MAX_TOKENS_RESPONSE

    def generate_digest(
        self, messages_text: str, system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate a digest from messages text.

        Args:
            messages_text: Combined text of all messages
            system_prompt: Optional custom system prompt

        Returns:
            Generated digest text
        """
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        user_prompt = self._create_user_prompt(messages_text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": user_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise RuntimeError(f"Cerebras API error: {e}")

    def generate_digest_map_reduce(
        self, message_chunks: List[str], system_prompt: Optional[str] = None
    ) -> str:
        """
        Generate digest using map-reduce approach for large datasets.

        Args:
            message_chunks: List of message text chunks
            system_prompt: Optional custom system prompt

        Returns:
            Final consolidated digest
        """
        if system_prompt is None:
            system_prompt = self._get_default_system_prompt()

        print(f"Processing {len(message_chunks)} chunks using map-reduce...")

        # Map phase: Generate partial summaries
        partial_summaries = []
        for i, chunk in enumerate(message_chunks, 1):
            print(f"  Processing chunk {i}/{len(message_chunks)}...")
            partial_prompt = self._create_user_prompt(
                chunk, is_partial=True, chunk_num=i, total_chunks=len(message_chunks)
            )

            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": partial_prompt},
                    ],
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )

                partial_summary = response.choices[0].message.content.strip()
                partial_summaries.append(partial_summary)

            except Exception as e:
                print(f"  Warning: Error processing chunk {i}: {e}")
                continue

        if not partial_summaries:
            raise RuntimeError("Failed to generate any partial summaries")

        # Reduce phase: Combine partial summaries
        print("  Combining partial summaries...")
        combined_text = "\n\n---\n\n".join(partial_summaries)
        reduce_prompt = self._create_reduce_prompt(combined_text)

        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": reduce_prompt},
                ],
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )

            return response.choices[0].message.content.strip()

        except Exception as e:
            raise RuntimeError(f"Error in reduce phase: {e}")

    @staticmethod
    def _get_default_system_prompt() -> str:
        """Get the default system prompt for digest generation."""
        return """You are an assistant for creating structured digests from Telegram channel posts about ML/AI.

IMPORTANT: Format for Telegram (no Markdown, plain text with emojis and structure).

Your task:
1. Analyze posts and group them by thematic categories
2. Create a brief summary for each category
3. List relevant posts with links for each category

Use the following categories (if information is available):
🔬 Research: scientific papers, research, preprints
🛠️ Tools: new tools, libraries, frameworks
📰 News: industry news, company announcements
📚 Tutorials: educational materials, tutorials, guides
💡 Other: everything else interesting

Output format for Telegram:
━━━━━━━━━━━━━━━━━━━━━
📊 ML/AI Digest — [dates]
━━━━━━━━━━━━━━━━━━━━━
Total posts: [number]

For each category:
🔬 Research
[2-4 sentences summary of key findings and developments]

• [Source] — Brief description
  🔗 [link]

• [Source] — Brief description
  🔗 [link]

🛠️ Tools
[Summary...]

• [Source] — Description
  🔗 [link]

Rules:
- Use line breaks for readability
- Use • for bullet points (not *, -, or numbers)
- Put links on separate lines with 🔗 emoji
- Use emojis for visual structure
- Keep it concise and scannable
- Preserve all original links
- No bold/italic/code formatting (Telegram won't render properly)"""

    @staticmethod
    def _create_user_prompt(
        messages_text: str, is_partial: bool = False, chunk_num: int = 1, total_chunks: int = 1
    ) -> str:
        """Create user prompt with messages."""
        if is_partial:
            intro = f"This is part {chunk_num} of {total_chunks} posts. Analyze and create a partial digest for this part:"
        else:
            intro = "Create a structured digest from the following posts:"

        return f"""{intro}

{messages_text}

IMPORTANT: Format for Telegram - use emojis, line breaks, • bullets, separate lines for links with 🔗. No Markdown formatting."""

    @staticmethod
    def _create_reduce_prompt(combined_summaries: str) -> str:
        """Create prompt for the reduce phase."""
        return f"""You have several partial digests below. Combine them into one final structured digest.

Tasks:
1. Merge similar topics and categories
2. Remove duplicates and repetitions
3. Create a unified brief summary for each category
4. Combine all source links
5. Preserve Telegram-friendly format

Partial digests:

{combined_summaries}

IMPORTANT: Create final digest using Telegram format:
- Use emojis for categories (🔬 🛠️ 📰 📚 💡)
- Use • for bullet points
- Put links on separate lines with 🔗
- Use line breaks for readability
- No Markdown formatting (no **, __, ```)"""


from typing import Optional
