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

IMPORTANT: Format for Telegram using Markdown.

Your task:
1. Analyze the content of posts and identify natural thematic categories
2. Group posts by these categories (don't force predetermined categories)
3. Create a brief summary for each category
4. List relevant posts with links for each category

Guidelines for categories:
- Identify 3-7 natural categories based on actual post content
- Use descriptive emoji that matches the category theme
- **Category names MUST be in the same language as the posts** (Russian posts → Russian categories, English posts → English categories)
- Category names should be clear and concise (1-3 words)
- Examples of possible categories (but adapt based on content):
  🔬 Research / 🛠️ Tools / 📰 News / 📚 Tutorials / 🚀 Releases
  💡 Insights / 🎯 Applications / 🔧 Infrastructure / 🌐 Community
  📊 Data / 🤖 Models / 💻 Code / 🎓 Education / etc.

Output format for Telegram (using Markdown):

**📊 ML/AI Digest — [date in format: DD Month YYYY]**

For each category you identified:

**[Emoji] [Category Name in same language as posts]**

📝 Brief summary (1-2 sentences) highlighting the main point.

||Detailed expandable summary (2-4 sentences) with comprehensive coverage of all key points. This gives readers full context if they want to dive deeper.||

[Source channel name](post_url)
[Source channel name](post_url)
[Source channel name](post_url)

(List Telegram post links, one per line. Use spoiler ||text|| for expandable detailed summary. If multiple posts from same channel, repeat channel name with different URLs)

[Next category without separator...]

Rules:
- Use **bold** for digest title and category names
- Use 📝 emoji before short summary (1-2 sentences, plain text)
- Add detailed summary in spoiler format: ||detailed text|| (this makes it expandable in Telegram)
- After summaries, list channel links normally: [Channel name](url)
- Format: [Channel name](telegram_post_url) - one link per line
- Include ONLY Telegram post links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If same channel has multiple posts, repeat channel name with different URLs
- Use line breaks for readability between categories (no separators)
- Categories should emerge from content, not be forced
- Category names in the same language as post content"""

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

IMPORTANT: Format for Telegram using Markdown:
- Category names in the SAME LANGUAGE as posts
- After category: short 📝 summary (1-2 sentences, main point only)
- Then: detailed summary in spoiler ||text|| format (2-4 sentences, comprehensive info)
- After summaries: list channel links normally: [Channel name](url)
- Format: [Channel name](telegram_post_url) on separate lines
- ONLY Telegram links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If same channel has multiple posts, repeat channel name with different URLs
- No separators between categories"""

    @staticmethod
    def _create_reduce_prompt(combined_summaries: str) -> str:
        """Create prompt for the reduce phase."""
        return f"""You have several partial digests below. Combine them into one final structured digest.

Tasks:
1. Identify and merge similar topics and categories across partial digests
2. Choose appropriate emojis for each merged category
3. Remove duplicates and repetitions
4. Create a unified brief summary for each final category
5. Combine all source links
6. Preserve Telegram-friendly format

Partial digests:

{combined_summaries}

IMPORTANT: Create final digest using Telegram Markdown format:
- Identify natural categories from the content (don't force predetermined ones)
- Category names in the SAME LANGUAGE as post content
- Use appropriate emojis for each category based on its theme
- Use **bold** for digest title and category names
- After category: short 📝 summary (1-2 sentences, main point only)
- Then: detailed summary in spoiler ||text|| format (2-4 sentences, comprehensive coverage)
- After summaries: list channel links normally: [Channel name](url)
- Format: [Channel name](telegram_post_url) on separate lines
- Include ONLY Telegram post links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If same channel has multiple posts, repeat channel name with different URLs
- Use line breaks between categories (NO separators like ━━━━)
- Categories should reflect the actual content, not predetermined templates"""


from typing import Optional
