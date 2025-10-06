# Quick Start

Step-by-step guide to run Telegram Digest PoC.

## Step 1: Install Dependencies

```bash
# Create virtual environment
python -m venv venv

# Activate it
source venv/bin/activate  # macOS/Linux
# or
venv\Scripts\activate  # Windows

# Install dependencies
pip install -r requirements.txt
```

## Step 2: Get API Credentials

### Telegram API

1. Go to https://my.telegram.org/apps
2. Log in with your phone number
3. Fill out the application creation form:
   - App title: "Telegram Digest" (or any name)
   - Short name: "digest" (or any short name)
   - Platform: choose appropriate (can be "Desktop")
4. Copy `api_id` (number) and `api_hash` (string)

### Cerebras API

1. Register at https://cloud.cerebras.ai/
2. After registration, go to API Keys section
3. Click "Create API Key"
4. Copy the key (it's shown only once!)

## Step 3: Configure .env File

```bash
# Copy example
cp .env.example .env

# Open .env in text editor
nano .env  # or use any editor
```

Fill in the following required fields:
```env
TELEGRAM_API_ID=12345678  # your api_id
TELEGRAM_API_HASH=abcdef1234567890abcdef1234567890  # your api_hash
CEREBRAS_API_KEY=csk-xxxxxxxxxxxxxxxxxxxxx  # your key
```

## Step 4: (Optional) Configure Channels

**Recommended**: Create `channels.yaml` for easier channel management:

```bash
# Copy example
cp channels.yaml.example channels.yaml

# Open channels.yaml in text editor
nano channels.yaml  # or use any editor
```

Edit with your channels:
```yaml
channels:
  - "@ai_news"
  - "@ml_research"
  - "@your_channel"

groups:
  news:
    - "@ai_news"
  
  research:
    - "@ml_research"
```

This allows running without --channels argument!

## Step 5: First Run

**With channels.yaml:**
```bash
python -m src.main
```

**Or specify channels directly:**
```bash
python -m src.main --channels @ai_news @ml_research --start-date 2025-10-04 --end-date 2025-10-05
```

**Authorization process:**
1. You'll be shown the phone number (the one linked to api_id)
2. Enter the code that will arrive in Telegram to this number
3. If you have two-factor authentication, enter your password

After first authorization, `telegram_session.session` file will be created - no need to enter code again.

## Step 5: Check Results

The script will do the following:
1. Connect to Telegram
2. Get messages from specified channels
3. Send them to Cerebras AI
4. Generate digest
5. Output result to console and save to file

## Usage Examples

### Basic Example (with channels.yaml)
```bash
python -m src.main
```

### Use Specific Group
```bash
python -m src.main --group research
```

### Override Channels
```bash
python -m src.main \
  --channels @ai_news @ml_research \
  --start-date 2025-10-01 \
  --end-date 2025-10-02
```

### Save to Specific File
```bash
python -m src.main \
  --channels @ai_news \
  --start-date 2025-10-01 \
  --end-date 2025-10-02 \
  --output-file my_digest.txt
```

### Send to Telegram Channel
```bash
python -m src.main \
  --channels @ai_news \
  --send-to-telegram \
  --telegram-target @my_digest_channel
```

## Troubleshooting

### "FloodWaitError"
Telegram limits request rate. Wait for the specified time.

### "ChannelPrivateError"
You don't have access to the channel. Make sure you're subscribed to the channel.

### "Invalid channel username"
Check that the channel name is correct and starts with @.

### "Cerebras API error"
- Check that the API key is correct
- Make sure you have API quota
- Check internet connection

## What's Next?

1. **Automation**: Set up cron for daily runs
2. **Customization**: Change prompts in `src/cerebras_client.py`
3. **Add channels**: Edit the list in command or in code
4. **Telegram bot**: Set up sending via bot (get token from @BotFather)

## Useful Links

- [Telethon Documentation](https://docs.telethon.dev/)
- [Cerebras API Docs](https://inference-docs.cerebras.ai/)
- [Telegram API](https://core.telegram.org/)
