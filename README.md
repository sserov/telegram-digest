# Telegram Digest PoC

Automated creation of structured digests from Telegram channel posts using Cerebras AI.

## Description

This project collects posts from specified Telegram channels over a defined period, sends them to an LLM (Cerebras) for analysis, and creates a structured digest organized by categories. The digest can be saved to a file or sent to a Telegram channel.

## Features

- 📥 Collect posts from multiple Telegram channels
- 📁 Support for Telegram folder invite links (automatic channel expansion)
- 📅 Filter posts by date (can specify a date range)
- 🤖 Generate structured digests using Cerebras AI
- 📊 Automatic grouping by categories with importance-based sorting
- 💾 Save digest to text file
- 📤 Send digest to Telegram via Bot API (HTML formatting)
- 🔄 Map-reduce processing for large data volumes
- ⏰ Automated daily generation via cron/scheduler
- 🐳 Docker support for easy deployment on VPS

## Requirements

### Local Installation
- Python 3.9+
- Telegram API credentials (api_id and api_hash) for reading messages
- Cerebras API key for AI digest generation
- Telegram Bot Token for sending digests (get from @BotFather)

### Docker Deployment (Recommended for VPS)
- Docker and Docker Compose
- VPS with SSH access
- Same credentials as above

## Quick Start

### Option 1: Docker on VPS (Recommended for Production)

**Note**: Docker is for VPS deployment only. For local development, use Option 2.

```bash
# On your VPS (not local machine):
# Clone repository
git clone https://github.com/sserov/telegram-digest.git
cd telegram-digest

# Configure
cp .env.example .env
cp channels.yaml.example channels.yaml
# Edit .env and channels.yaml with your credentials

# Build and run
docker-compose build
./docker-run.sh
```

See **[VPS_QUICKSTART.md](VPS_QUICKSTART.md)** for 5-minute VPS setup or **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** for complete guide.

### Option 2: Local Python (For Development and Local Use)

## Installation

1. Clone the repository:
```bash
cd telegram-digest
```

2. Create a virtual environment:
```bash
python -m venv venv
source venv/bin/activate  # On Windows: venv\Scripts\activate
```

3. Install dependencies:
```bash
pip install -r requirements.txt
```

4. Create `.env` file based on `.env.example`:
```bash
cp .env.example .env
```

5. Fill in `.env` with your credentials:
```env
# Telegram API (get from https://my.telegram.org/apps)
TELEGRAM_API_ID=your_api_id
TELEGRAM_API_HASH=your_api_hash

# Cerebras AI API (get from https://cloud.cerebras.ai/)
CEREBRAS_API_KEY=your_cerebras_api_key

# Telegram Bot Token (required for sending digests to Telegram)
# Get from @BotFather: https://t.me/BotFather
TELEGRAM_BOT_TOKEN=your_bot_token

# (Optional) Channel for publishing digest
OUTPUT_TELEGRAM_CHANNEL=@your_channel
```

6. **(Recommended)** Create `channels.yaml` from example:
```bash
cp channels.yaml.example channels.yaml
```

Edit `channels.yaml` with your channels:
```yaml
channels:
  - "@ai_news"
  - "@ml_research"
  - "@your_channel"
  # Or use Telegram folder invite links
  - "https://t.me/addlist/YourFolderSlug"

groups:
  news:
    - "@ai_news"
    - "@tech_digest"
    # Folder links work in groups too
    - "https://t.me/addlist/NewsChannelsFolder"
  
  research:
    - "@ml_research"
    - "@arxiv_daily"
```

**Note:** You can use Telegram folder invite links (e.g., `https://t.me/addlist/Wv30yLzHEuw4YTky`) to automatically include all channels from a shared folder. This is useful for managing large channel collections.

## Usage

### Basic Usage (with channels.yaml)

Create a digest for today using channels from config:
```bash
python -m src.main
```

### Use Specific Channel Group

```bash
python -m src.main --group research
```

### Override with CLI Arguments

```bash
python -m src.main --channels @ai_news @ml_research @deeplearning
```

You can also use folder links directly in CLI:

```bash
python -m src.main --channels "https://t.me/addlist/Wv30yLzHEuw4YTky"
```

Or mix channels and folder links:

```bash
python -m src.main --channels @ai_news "https://t.me/addlist/FolderSlug" @ml_research
```

### Specify Channels and Dates

```bash
python -m src.main \
  --channels @ai_news @ml_research @deeplearning \
  --start-date 2025-10-01 \
  --end-date 2025-10-03
```

### Use Custom Config File

```bash
python -m src.main --config my_channels.yaml --group news
```

### Save to File

```bash
python -m src.main \
  --channels @ai_news @ml_research \
  --output-file digest_2025-10-05.txt
```

### Send to Telegram

Sends digest to Telegram via Bot API (requires `TELEGRAM_BOT_TOKEN` in `.env`):

```bash
python -m src.main \
  --send-to-telegram \
  --telegram-target @my_digest_channel
```

Note: Digest is formatted using HTML markup (bold, links, blockquotes).

### All Options

```bash
python -m src.main --help
```

## Automated Daily Generation

You can set up automatic daily digest generation using cron.

### Quick Setup

1. Create your script from the example:
   ```bash
   cp run_digest.sh.example run_digest.sh
   # Edit run_digest.sh with your paths
   chmod +x run_digest.sh
   ./run_digest.sh  # Test it
   ```

2. Set up daily execution at 22:00 (10 PM):
   ```bash
   (crontab -l 2>/dev/null; echo "0 22 * * * /path/to/telegram-digest/run_digest.sh >> /path/to/telegram-digest/cron.log 2>&1") | crontab -
   ```

3. Verify cron job:
   ```bash
   crontab -l
   ```

4. Check logs:
   ```bash
   tail -f cron.log
   ```

**⚠️ macOS Users**: If you get "Operation not permitted" errors, you need to grant Full Disk Access to cron in System Settings → Privacy & Security → Full Disk Access → add `/usr/sbin/cron`.

For detailed setup instructions and troubleshooting, see [CRON_SETUP.md](CRON_SETUP.md).

## Configuration

Main settings in `src/config.py`:

- `MAX_TOKENS_PER_CHUNK`: maximum tokens per chunk (default 50000)
- `TEMPERATURE`: generation temperature (default 0.0)
- `MAX_TOKENS_RESPONSE`: maximum response length (default 4000)

## LLM Provider Support

As of v0.7.0, the system supports **any OpenAI-compatible LLM API provider**. Switch providers by editing `.env`:

### Supported Providers

| Provider | URL | Model Examples | Speed | Cost | Best For |
|----------|-----|---|-------|------|----------|
| **Cerebras** | `https://api.cerebras.ai/v1` | `llama3.1-70b` | Fast | Premium | Quality outputs, high context |
| **Groq** | `https://api.groq.com/openai/v1` | `mixtral-8x7b-32768` | ⚡ Fastest | Free tier | Fast processing, cost-effective |
| **Together AI** | `https://api.together.xyz/v1` | `meta-llama/Llama-3-70b-chat-hf` | Fast | Paid | Flexible model selection |
| **OpenAI** | `https://api.openai.com/v1` | `gpt-4-turbo` | Standard | Expensive | High quality (GPT-4) |
| **Local** | `http://localhost:8000/v1` | Your local models | Variable | Free | Self-hosted, privacy |

### How to Switch Providers

1. Get API credentials from your chosen provider
2. Update these variables in `.env`:
   ```ini
   LLM_PROVIDER=groq
   LLM_API_URL=https://api.groq.com/openai/v1
   LLM_API_KEY=gsk_...your-groq-key...
   LLM_MODEL=mixtral-8x7b-32768
   ```
3. Run normally - **no code changes needed!**

### Example: Using Groq

```bash
# Update .env
sed -i 's/LLM_PROVIDER=cerebras/LLM_PROVIDER=groq/' .env
sed -i 's|LLM_API_URL=.*|LLM_API_URL=https://api.groq.com/openai/v1|' .env
sed -i 's/LLM_API_KEY=.*/LLM_API_KEY=gsk_your_groq_key/' .env
sed -i 's/LLM_MODEL=.*/LLM_MODEL=mixtral-8x7b-32768/' .env

# Run digest generation
python -m src.main --channels @your_channel
```

### Backward Compatibility

- If `LLM_API_KEY` is not set, falls back to `CEREBRAS_API_KEY`
- If `LLM_MODEL` is not set, falls back to `CEREBRAS_MODEL`
- Existing configurations continue to work without changes

## Project Structure

```
telegram-digest/
├── src/
│   ├── __init__.py
│   ├── main.py              # Entry point
│   ├── config.py            # Configuration
│   ├── llm_client.py        # OpenAI-compatible LLM client (provider-agnostic)
│   ├── telegram_fetcher.py  # Collect posts from Telegram
│   ├── llm_adapter.py       # Adapter for digest generation
│   ├── digest_generator.py  # Digest generation
│   └── output_handler.py    # Save and send results
├── requirements.txt
├── .env.example
├── .gitignore
└── README.md
```

## Digest Format

The digest is automatically structured with AI-identified categories based on content.  
Uses **HTML formatting** when sent to Telegram (converted from Markdown internally):

- **Bold** for category names and headlines
- Clickable links to source posts
- `<blockquote>` for detailed summaries
- Categories and news sorted by importance

```
**📊 ML/AI Digest — 06 October 2025**

**🔬 Прорывы в исследованиях**

📝 *GPT-5 впервые решила две сложные академические задачи, подтвердив рост ИИ в логическом и математическом мышлении.*

1. **[GPT-5 решила задачу уровня IMO](https://t.me/data_secrets/7955)** — Первая LLM, решившая сложную математическую задачу
   *[Data Secrets, 06.10.2025]*

2. **[Опровержение гипотезы в теории информации](https://t.me/data_secrets/7955)** — Найден контрпример для систем передачи данных
   *[Data Secrets, 06.10.2025]*

**🛠️ Новые продукты**

📝 *OpenAI готовится представить Agent Builder — инструмент для создания ИИ-агентов без программирования.*

1. **[OpenAI Agent Builder анонсирован](https://t.me/data_secrets/7957)** — Low-code платформа для оркестрации агентов
   *[Data Secrets, 06.10.2025]*

**🧑‍💼 Кадровые перемены**

📝 *Anthropic укрепляет техническое руководство, делая ставку на инфраструктуру.*

1. **[Рахул Патил стал CTO Anthropic](https://t.me/data_secrets/7958)** — Фокус на инфраструктуре и вычислениях
   *[Data Secrets, 06.10.2025]*
```

**Key features:**
- **Bold** headers and category names
- 📝 *Italic* category summaries for clear separation
- **Clickable post titles** as hyperlinks
- *Italic* source attribution
- Numbered lists for posts within categories
- No visual separators - clean line breaks
- Dynamic categories based on content
- Category names in same language as posts

## Getting Telegram API Credentials

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Create a new application
4. Copy `api_id` and `api_hash`

## Getting Cerebras API Key

1. Register at https://cloud.cerebras.ai/
2. Go to API Keys section
3. Create a new key
4. Copy the key to `.env`

## Limits and Restrictions

- **Telegram API**: Rate limits on reading messages (usually not a problem for reading)
- **Cerebras API**: Check your plan limits
- **Context size**: Automatically uses map-reduce for large volumes

## Security

⚠️ **Important:**
- Never commit `.env` file
- Keep API keys secure
- Telegram session file (`telegram_session.session`) also contains sensitive data

## Troubleshooting

### "No messages found for the specified date range"
- Check that channels are specified correctly (with @ for public channels)
- Make sure dates are in YYYY-MM-DD format
- Verify that your account has access to the channels

### "Cerebras API error"
- Check that `CEREBRAS_API_KEY` is specified correctly
- Make sure you have API access
- Check your account limits

### "Telethon authorization error"
- On first run, you'll need to enter a code from Telegram
- Make sure `api_id` and `api_hash` are correct

## Digest Examples

After generation, you'll receive a structured digest:

```
📊 ML/AI Digest — October 4, 2025
==================================================
Total posts: 15

🔬 Research
New research published on improving transformer model efficiency 
and applying RL in robotics. Zero-shot learning results presented.

• @ai_research (2025-10-04): New paper on efficient transformers - https://t.me/ai_research/123
• @ml_papers (2025-10-04): RL breakthrough in robotics - https://t.me/ml_papers/456
• @deeplearning (2025-10-04): Zero-shot learning advances - https://t.me/deeplearning/789

🛠️ Tools
New versions of popular ML libraries announced and PyTorch updates.

• @ml_tools (2025-10-04): PyTorch 2.1 released - https://t.me/ml_tools/321
• @python_ai (2025-10-04): New scikit-learn features - https://t.me/python_ai/654

📰 News
OpenAI announced new GPT capabilities, Google announced Gemini updates.

• @ai_news (2025-10-04): OpenAI GPT updates - https://t.me/ai_news/111
• @tech_news (2025-10-04): Google Gemini improvements - https://t.me/tech_news/222
```

## Architecture

The project follows a modular architecture:

```
User Input → TelegramFetcher → Messages → DigestGenerator
                                              ↓
                                         LLMClient
                                              ↓
                                       Generated Digest
                                              ↓
                                         OutputHandler → File/Telegram/Console
```

See `ARCHITECTURE.md` for more details

## Performance

- **Single-pass**: Processing < 200K characters (~50K tokens) in 10-30 seconds
- **Map-reduce**: Automatically for large volumes, time proportional to number of chunks
- **Memory**: Efficient usage through iterators and async
- **Rate limits**: Respects Telegram and Cerebras API limits

## Contributing

Contributions are welcome! Please:

1. Follow existing code style (PEP 8)
2. Add docstrings to new functions
3. Update documentation
4. Test changes before submitting

## Roadmap

### v0.2.0 (Near future)
- [ ] Unit tests
- [ ] Custom categories via config
- [ ] Progress bars
- [ ] Improved logging

### v0.3.0
- [ ] SQLite for message caching
- [ ] Private channel support
- [ ] Scheduler for automatic digests
- [ ] Support for other LLM providers

### v1.0.0
- [ ] Web UI
- [ ] Multi-user support
- [ ] Database for history
- [ ] Analytics and statistics

## Acknowledgments

- [Telethon](https://github.com/LonamiWebs/Telethon) - Excellent Telegram library
- [Cerebras](https://cerebras.ai/) - Fast and efficient LLM inference
- Telegram for the great API

## License

MIT License - see [LICENSE](LICENSE)

## Contact

If you have questions or suggestions:
- Create an Issue in the repository
- See documentation below

## Documentation

- **[QUICKSTART.md](QUICKSTART.md)** - Quick start guide for local setup
- **[DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md)** - Complete Docker deployment guide for VPS
- **[VPS_QUICKSTART.md](VPS_QUICKSTART.md)** - Fast VPS deployment in 5 minutes
- **[DOCKER.md](DOCKER.md)** - Docker files overview and troubleshooting
- **[DEVELOPMENT.md](DEVELOPMENT.md)** - Development setup and contribution guide
- **[ARCHITECTURE.md](ARCHITECTURE.md)** - System architecture and design
- **[CRON_SETUP.md](CRON_SETUP.md)** - Cron scheduling guide (local/VPS)
- **[PROVIDER_SWITCHING.md](PROVIDER_SWITCHING.md)** - Provider switching guide
- **[CHANGELOG.md](CHANGELOG.md)** - Version history and changes

## Author

Created as a PoC for automated Telegram digest generation with Cerebras AI.

**Version**: 0.7.0  
**Status**: Production-ready  
**Last Updated**: September 2026
