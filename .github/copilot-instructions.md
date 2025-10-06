# GitHub Copilot Instructions

## Project Overview

This is a Telegram Digest Generator that collects posts from Telegram channels, analyzes them using Cerebras AI, and generates structured digests organized by categories with importance-based sorting.

## Tech Stack

- **Python 3.9+**: Main language
- **Telethon**: Telegram API client (for reading messages only)
- **Cerebras Cloud SDK**: LLM for digest generation
- **Telegram Bot API**: HTTP requests for sending digests (HTML formatting)
- **requests**: For Bot API HTTP calls

## Architecture Principles

### Core Components

1. **TelegramFetcher** (`telegram_fetcher.py`): Reads messages from channels using Telethon
2. **CerebrasClient** (`cerebras_client.py`): Generates digests using LLM
3. **DigestGenerator** (`digest_generator.py`): Orchestrates the digest creation process
4. **OutputHandler** (`output_handler.py`): Saves to files and sends via Bot API
5. **Config** (`config.py`): Centralized configuration and environment variables

### Message Sending

**IMPORTANT**: Only use Telegram Bot API for sending messages:
- Use `OutputHandler.send_via_bot_api()` method
- Format: Markdown internally, converted to HTML for sending
- Direct HTTP POST to `https://api.telegram.org/bot{TOKEN}/sendMessage`
- Parse mode: `"HTML"` (not MarkdownV2)
- No Telethon for sending (removed in v0.4.0)

### Formatting Rules

**Markdown Format (internal)**:
```markdown
**bold text**
[link text](url)
>quote text
```

**HTML Conversion (for Telegram)**:
- `**text**` → `<b>text</b>`
- `[text](url)` → `<a href="url">text</a>`
- `>quote` → `<blockquote>quote</blockquote>`
- Escape only: `& < >` using `html.escape()`

**Never use**:
- MarkdownV2 with complex escaping
- Telethon for sending messages
- `parse_mode="MarkdownV2"`

### Digest Structure

```
**📊 ML/AI Digest — DD Month YYYY**

**[Emoji] Category Name**

🔹 **News Headline**

>Optional detailed summary (2-4 sentences)

[Source Channel](post_url)
[Source Channel](post_url)
```

**Key Requirements**:
- Categories sorted by importance (groundbreaking > releases > tools > discussions)
- News items within categories sorted by importance
- Category names in the same language as posts
- No separators between categories
- Link previews disabled (`disable_web_page_preview: True`)

## Code Style Guidelines

### General Python

- Use type hints for all function parameters and return values
- Docstrings in Google style for all public methods
- Async/await for I/O operations (except Bot API which is sync HTTP)
- Error handling with specific exceptions
- Environment variables via `Config` class

### Naming Conventions

- Classes: `PascalCase` (e.g., `TelegramFetcher`)
- Functions/methods: `snake_case` (e.g., `fetch_messages`)
- Constants: `UPPER_SNAKE_CASE` (e.g., `MAX_TOKENS`)
- Private methods: `_leading_underscore` (e.g., `_send_via_bot_api`)

### Error Handling

```python
try:
    response = requests.post(url, json=payload, timeout=30)
    result = response.json()
    if result.get("ok"):
        print("✅ Success message")
        return True
    else:
        error_desc = result.get('description', 'Unknown error')
        print(f"❌ Error: {error_desc}")
        return False
except requests.exceptions.RequestException as e:
    print(f"❌ Failed: {e}")
    return False
```

### Configuration

Always use `Config` class for settings:
```python
from .config import Config

# Good
token = Config.TELEGRAM_BOT_TOKEN
url = f"https://api.telegram.org/bot{Config.TELEGRAM_BOT_TOKEN}/sendMessage"

# Bad - never hardcode
token = os.getenv('TELEGRAM_BOT_TOKEN')
```

## Common Patterns

### Adding New Output Formats

When adding new output methods:
1. Add to `OutputHandler` class
2. Keep it simple and focused
3. Use async only for I/O operations
4. Return `bool` for success/failure

### Extending Prompts

When modifying LLM prompts in `CerebrasClient`:
1. Keep system prompt clear and structured
2. Use explicit formatting rules
3. Include examples for clarity
4. Test with different content types

### Message Processing

For large datasets:
1. Use `generate_digest_map_reduce()` for >50k tokens
2. Split on message boundaries, not mid-message
3. Preserve context in chunks

## Testing Approach

### Manual Testing Commands

```bash
# Basic test
python -m src.main --channels @channel_name

# Send to Telegram
python -m src.main --send-to-telegram --telegram-target @test_channel

# Date range
python -m src.main --start-date 2025-10-06 --end-date 2025-10-07
```

### What to Test

- [ ] Message fetching from multiple channels
- [ ] Digest generation with different content volumes
- [ ] HTML conversion (bold, links, quotes)
- [ ] Long message splitting (>4000 chars)
- [ ] Bot API sending with proper formatting
- [ ] Error handling (network, API limits, etc.)

## Common Pitfalls to Avoid

### ❌ Don't Do This

```python
# Don't use Telethon for sending
await client.send_message(target, digest, parse_mode='MarkdownV2')

# Don't use MarkdownV2 escaping
text.replace('-', r'\-').replace('.', r'\.')

# Don't hardcode configuration
CEREBRAS_API_KEY = "sk-..."

# Don't mix Markdown and HTML
result.append('<b>**text**</b>')  # Wrong!
```

### ✅ Do This Instead

```python
# Use Bot API via HTTP
OutputHandler.send_via_bot_api(digest, target)

# Use HTML formatting
html_text = OutputHandler.markdown_to_html(digest)

# Use Config class
api_key = Config.CEREBRAS_API_KEY

# Convert Markdown to HTML properly
result.append('<b>text</b>')  # Correct!
```

## Environment Variables

Required:
- `TELEGRAM_API_ID`: Telegram API ID (for reading)
- `TELEGRAM_API_HASH`: Telegram API hash (for reading)
- `CEREBRAS_API_KEY`: Cerebras AI API key
- `TELEGRAM_BOT_TOKEN`: Bot token (for sending via Bot API)

Optional:
- `OUTPUT_TELEGRAM_CHANNEL`: Default output channel
- `CEREBRAS_MODEL`: Model name (default: llama3.1-70b)
- `TEMPERATURE`: Generation temperature (default: 0.0)

## File Structure

```
telegram-digest/
├── .github/
│   └── copilot-instructions.md  ← This file
├── src/
│   ├── main.py                  ← Entry point, CLI args
│   ├── config.py                ← Configuration management
│   ├── telegram_fetcher.py      ← Fetch messages (Telethon)
│   ├── cerebras_client.py       ← LLM client
│   ├── digest_generator.py      ← Orchestration
│   └── output_handler.py        ← Output (file, Bot API)
├── .env                         ← Environment variables (not in git)
├── channels.yaml                ← Channel list (optional)
└── requirements.txt             ← Dependencies
```

## Dependencies

When adding new dependencies:
1. Add to `requirements.txt` with version constraint
2. Keep minimal - avoid unnecessary packages
3. Prefer standard library when possible
4. Document why the dependency is needed

## Current Known Limitations

1. Bot API has 4096 character limit per message (handled by splitting)
2. Telethon rate limits apply to message fetching
3. Cerebras API context window limits (handled by map-reduce)
4. HTML formatting in Telegram has specific quirks (test thoroughly)

## Future Enhancements (Do Not Implement Yet)

- SQLite caching for messages
- Web UI for configuration
- More output formats (PDF, JSON, etc.)
- Scheduled digest generation
- Multi-language support beyond auto-detection

## Questions?

Refer to:
- `ARCHITECTURE.md` for system design
- `DEVELOPMENT.md` for development setup
- `README.md` for user-facing docs
- `CHANGELOG.md` for version history
