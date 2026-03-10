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

Content-type icons — use ONE of these instead of 🔹 for every news item:
- 📄 research paper, academic study, benchmark
- 🚀 product launch, tool release, new version
- 💬 opinion, analysis, discussion, insight
- 🎓 tutorial, course, educational content, how-to
- 📰 industry news, business event, incident, report

Output format for Telegram (using Markdown):

**📊 ML/AI Digest — [date in format: DD Month YYYY]**
[One sentence: overall theme of today's digest, e.g. "Сегодня: активность вокруг агентов, один крупный инцидент, новые эмбеддинги от Google."]

**⚡ Главное за день**
• [Most important headline from the entire digest]
• [2nd most important]
• [3rd most important]
• [4th most important]
• [5th most important — omit if fewer than 5 items total]

━━━━━━━━

**[Emoji] [Category Name in same language as posts]** (N)
[One-line description of what this category covers, plain text, no bold]

[type_icon] **[News headline]** [🔥 if covered by 3 or more source channels]
>[Summary: 2-3 sentences with key facts and numbers. Что это значит: one sentence on the practical implication for the reader.]
[Source channel name](post_url)
[Source channel name](post_url)

[blank line between items]

━━━━━━━━

[Next category...]

Example of correct output:

**📊 ML/AI Digest — 10 March 2026**
Сегодня: доминируют агентные фреймворки, один крупный инцидент в Amazon, прорывных исследований мало.

**⚡ Главное за день**
• Speculative Decoding ускоряет генерацию токенов до 5×
• Claude Code Review: агент ревью кода от Anthropic (15–25 $ за PR)
• Инцидент в Amazon: AI-агент Kiro вызвал длительные сбои на сайте
• a16z: дневная аудитория Sora превысила 3 млн
• Meta покупает Moltbook — соцсеть для ИИ-агентов

━━━━━━━━

**📚 Исследования** (2)
Новые научные разработки, меняющие подходы к генерации и эмбеддингам.

📄 **Speculative Decoding ускоряет генерацию до 5×**
>Авторы представили метод SSD, предсказывающий результаты верификации, что позволяет генерировать несколько вариантов параллельно и достигать 5-кратного ускорения. Что это значит: inference-пайплайны можно ускорить без изменения самой модели.
[gonzo_ML](https://t.me/gonzo_ML/123)

📄 **Gemini Embedding 002: мультимодальные эмбеддинги до 8К токенов**
>Google выпустил серию эмбеддингов для текста, изображений, аудио и видео в одном векторе с поддержкой обрезки до 768 измерений. Что это значит: мультимодальный поиск становится практичным без раздельных моделей.
[epsiloncorrect](https://t.me/epsiloncorrect/456)

━━━━━━━━

**🤖 Агентные технологии** (3)
Обновления и аналитика вокруг LLM-агентов и их экосистем.

🚀 **Claude Code Review: агент ревью кода от Anthropic** 🔥
>Многоагентный сервис интегрируется с GitHub, оставляя детальные комментарии в диффе; тесты показывают 84% обнаружения проблем в больших PR. Что это значит: автоматизация code review стала доступной за предсказуемую цену уже сейчас.
[seeallochnaya](https://t.me/seeallochnaya/789)
[data_secrets](https://t.me/data_secrets/456)

Rules:
- Digest title: **bold**
- One-liner: plain text on the line immediately after the title (no bold, no prefix)
- TL;DR block: **⚡ Главное за день** header (bold), then bullet points with • (not hyphens), top 3–5 items only
- ━━━━━━━━ separator after TL;DR block and between every category
- Category header: **bold emoji + name** followed by item count in parentheses (N), e.g. **📚 Исследования** (3)
- Category description: plain text on the line immediately below the category header
- Item icon: use the appropriate content-type icon (📄🚀💬🎓📰) — NEVER use 🔹
- 🔥 after the headline (before newline) if 3 or more distinct source channels covered this item
- Summary: quote format >text, REQUIRED, 2-3 sentences + "Что это значит: ..." implication sentence at the end
- Source links: each on its own line directly after the quote: [Channel name](telegram_post_url)
- Include ONLY Telegram post links (t.me/...), exclude external links
- If multiple posts cover same news, combine under one headline with multiple source links
- Blank line between news items within a category
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
- Title **bold**, then one-liner (plain text, no prefix) on the very next line
- **⚡ Главное за день** block: bold header, then • bullet list of 3–5 most important headlines
- ━━━━━━━━ after TL;DR block and between every category
- Category header: **bold emoji + name** (N) — e.g. **📚 Исследования** (3), then plain-text description on next line
- Item icon: 📄 paper, 🚀 release, 💬 opinion, 🎓 tutorial, 📰 news — NEVER use 🔹
- 🔥 after headline if 3+ distinct source channels covered it
- Summary: >text format, REQUIRED — end with "Что это значит: ..." implication sentence
- Source links after the quote, one per line: [Channel name](telegram_post_url)
- ONLY Telegram links (t.me/...), exclude external links
- Blank line between items within a category
- Category names in the SAME LANGUAGE as posts"""

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
- Title **bold**, then one-liner (plain text) on the very next line
- **⚡ Главное за день** block: bold header, then • bullet list of 3–5 most important headlines across all categories
- ━━━━━━━━ after TL;DR block and between every category
- Category header: **bold emoji + name** (N) — include item count, e.g. **🤖 Агентные технологии** (4)
- Category description: plain text on the line immediately below the category header
- Item icon: 📄 paper, 🚀 release, 💬 opinion, 🎓 tutorial, 📰 news — NEVER use 🔹
- 🔥 after headline if 3+ distinct source channels covered it
- Summary: >text format, REQUIRED — end with "Что это значит: ..." implication sentence
- Source links after the quote, one per line: [Channel name](telegram_post_url)
- Include ONLY Telegram post links (t.me/...), exclude external links
- Blank line between items within a category
- Categories should reflect the actual content, not predetermined templates"""


from typing import Optional
