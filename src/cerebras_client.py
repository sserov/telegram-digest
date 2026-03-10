"""Cerebras AI client for digest generation."""

import time
from typing import List, Dict, Any, Optional
from cerebras.cloud.sdk import Cerebras

from .config import Config

_RETRY_DELAYS = [30, 60, 120]  # seconds to wait between retries on 429


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

        return self._call_with_retry(
            messages=[
                {"role": "system", "content": system_prompt},
                {"role": "user", "content": user_prompt},
            ]
        )

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
                partial_summary = self._call_with_retry(
                    messages=[
                        {"role": "system", "content": system_prompt},
                        {"role": "user", "content": partial_prompt},
                    ]
                )
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
            return self._call_with_retry(
                messages=[
                    {"role": "system", "content": system_prompt},
                    {"role": "user", "content": reduce_prompt},
                ]
            )

        except Exception as e:
            raise RuntimeError(f"Error in reduce phase: {e}")

    def _call_with_retry(self, messages: List[Dict[str, str]]) -> str:
        """Call Cerebras API with retry on 429 rate limit errors."""
        for attempt, delay in enumerate(_RETRY_DELAYS, 1):
            try:
                response = self.client.chat.completions.create(
                    model=self.model,
                    messages=messages,
                    temperature=self.temperature,
                    max_tokens=self.max_tokens,
                )
                return response.choices[0].message.content.strip()
            except Exception as e:
                error_str = str(e)
                if "429" in error_str or "rate" in error_str.lower() or "too many" in error_str.lower():
                    print(f"⚠️  Rate limit hit (attempt {attempt}/{len(_RETRY_DELAYS)}). Waiting {delay}s...")
                    time.sleep(delay)
                else:
                    raise RuntimeError(f"Cerebras API error: {e}")

        # Final attempt after all retries
        try:
            response = self.client.chat.completions.create(
                model=self.model,
                messages=messages,
                temperature=self.temperature,
                max_tokens=self.max_tokens,
            )
            return response.choices[0].message.content.strip()
        except Exception as e:
            raise RuntimeError(f"Cerebras API error after {len(_RETRY_DELAYS)} retries: {e}")

    @staticmethod
    def _get_default_system_prompt() -> str:
        """Get the default system prompt for digest generation."""
        return """You are an assistant for creating structured digests from Telegram channel posts about ML/AI.

IMPORTANT: Format for Telegram using Markdown.

Your task:
1. Analyze the content of posts and identify natural thematic categories
2. Group posts by these categories (don't force predetermined categories)
3. For each category, identify individual news items (can combine related posts)
4. Sort categories by importance (impact, novelty, relevance)
5. Sort news items within each category by importance
6. Create concise headlines and summaries for each news item

Guidelines for categories:
- Identify 3-7 natural categories based on actual post content
- Use descriptive emoji that matches the category theme
- **Category names MUST be in the same language as the posts** (Russian posts → Russian categories, English posts → English categories)
- Category names should be clear and concise (1-3 words)
- Sort by importance: groundbreaking research > major releases > tools/tutorials > discussions
- Examples of possible categories (but adapt based on content):
  🔬 Research / 🛠️ Tools / 📰 News / 📚 Tutorials / 🚀 Releases
  💡 Insights / 🎯 Applications / 🔧 Infrastructure / 🌐 Community
  📊 Data / 🤖 Models / 💻 Code / 🎓 Education / etc.

Output format for Telegram (using Markdown):

**📊 ML/AI Digest — [date in format: DD Month YYYY]**

For each category (separated from the previous one by ━━━━━━━━):

**[Emoji] [Category Name in same language as posts]**
[One-line description of what this category covers, plain text, no bold]

For each news item in this category (blank line between items):

🔹 **[News headline - concise title for this news item]**
>[Summary: 2-3 sentences with key facts, numbers, and context]
[Source channel name](post_url)
[Source channel name](post_url)

Example of correct output:

**📊 ML/AI Digest — 10 March 2026**

**📚 Исследования**
Новые научные разработки, меняющие подходы к генерации и эмбеддингам.

🔹 **Speculative Decoding ускоряет генерацию до 5×**
>Авторы представили метод SSD, который предсказывает результаты верификации и генерирует несколько вариантов параллельно, достигая 5-кратного ускорения по сравнению с авторегрессивным декодированием.
[gonzo_ML](https://t.me/gonzo_ML/123)

🔹 **Gemini Embedding 002: мультимодальные эмбеддинги до 8К токенов**
>Google выпустил новую серию эмбеддингов, поддерживающих текст, изображения, аудио и видео в одном векторе.
[epsiloncorrect](https://t.me/epsiloncorrect/456)

━━━━━━━━

**🤖 Агентные технологии**
Обновления и аналитика вокруг LLM-агентов и их экосистем.

🔹 **Claude Code Review: агент ревью кода от Anthropic**
>Новый многоагентный сервис интегрируется с GitHub, автоматически оставляя детальные комментарии в диффе.
[seeallochnaya](https://t.me/seeallochnaya/789)

Rules:
- Use **bold** for digest title and category names only
- Category description: plain text on the line immediately below the bold category header
- For each news item: 🔹 + **bold headline** on one line, then >summary on next line, then source links
- Summary in quote format >text is REQUIRED for every news item (2-3 sentences, include concrete numbers/facts)
- Source links come directly after the quote, each on its own line: [Channel name](telegram_post_url)
- Include ONLY Telegram post links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If multiple posts cover same news, combine under one headline with multiple source links
- Blank line between news items within a category
- ━━━━━━━━ separator between categories (not before the first category, not after the last)
- Sort categories by importance (most impactful first)
- Sort news items within each category by importance
- Categories should emerge from content, not be forced
- Category names and headlines in the same language as post content"""

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
- Category header: **bold**, then on the NEXT LINE a plain-text one-line description (no bold, no 📝 prefix)
- For each news item: 🔹 **bold headline**, then >summary (2-3 sentences, required), then source links
- Summary MUST be in quote format: >text — do NOT skip it
- Source links on separate lines after the quote: [Channel name](telegram_post_url)
- ONLY Telegram links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If same channel has multiple posts, repeat channel name with different URLs
- Blank line between news items within a category
- ━━━━━━━━ separator line between categories (not before first, not after last)"""

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
- Use **bold** for digest title and category names only
- Category header: **bold**, then on the NEXT LINE a plain-text one-line description (no bold, no 📝 prefix)
- For each news item: 🔹 **bold headline**, then >summary (2-3 sentences, required), then source links
- Summary MUST be in quote format: >text — do NOT skip it
- Source links on separate lines after the quote: [Channel name](telegram_post_url)
- Include ONLY Telegram post links (t.me/...), exclude external links (twitter, arxiv, github, etc.)
- If same channel has multiple posts, repeat channel name with different URLs
- Blank line between news items within a category
- ━━━━━━━━ separator line between categories (not before first, not after last)
- Categories should reflect the actual content, not predetermined templates"""


from typing import Optional
