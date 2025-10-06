# Development Guide

## Project Structure

```
telegram-digest/
├── src/
│   ├── __init__.py           # Package initialization
│   ├── main.py               # CLI entry point
│   ├── config.py             # Configuration management
│   ├── telegram_fetcher.py   # Telegram API integration
│   ├── cerebras_client.py    # Cerebras AI client
│   ├── digest_generator.py   # Digest generation logic
│   └── output_handler.py     # Output handling (file, Telegram)
├── example_usage.py          # Usage examples
├── requirements.txt          # Python dependencies
├── .env.example              # Environment variables template
├── .gitignore                # Git ignore rules
├── README.md                 # Main documentation
├── QUICKSTART.md             # Quick start guide
└── DEVELOPMENT.md            # This file
```

## Architecture

### Components

1. **TelegramFetcher** (`telegram_fetcher.py`)
   - Handles Telegram API authentication
   - Fetches messages from specified channels
   - Filters messages by date range
   - Extracts URLs and metadata

2. **CerebrasClient** (`cerebras_client.py`)
   - Integrates with Cerebras AI API
   - Manages prompts for digest generation
   - Handles map-reduce for large datasets

3. **DigestGenerator** (`digest_generator.py`)
   - Orchestrates message processing
   - Decides between single-pass and map-reduce
   - Formats final digest

4. **OutputHandler** (`output_handler.py`)
   - Saves digest to files
   - Sends digest to Telegram via Bot API (HTTP requests with HTML formatting)
   - Handles long messages (splitting)
   - Converts Markdown to HTML for Telegram

5. **Config** (`config.py`)
   - Centralizes configuration
   - Validates environment variables
   - Provides utility functions

### Data Flow

```
1. User Input (CLI or API)
   ↓
2. TelegramFetcher.fetch_messages()
   ↓
3. DigestGenerator.generate_digest()
   ↓
4. CerebrasClient.generate_digest() or generate_digest_map_reduce()
   ↓
5. OutputHandler (save to file / send to Telegram)
```

## Configuration

### Environment Variables

Required:
- `TELEGRAM_API_ID`: Your Telegram API ID
- `TELEGRAM_API_HASH`: Your Telegram API hash
- `CEREBRAS_API_KEY`: Your Cerebras API key

Optional:
- `TELEGRAM_BOT_TOKEN`: Bot token for sending digests (required for Telegram output)
- `OUTPUT_TELEGRAM_CHANNEL`: Default output channel
- `CEREBRAS_MODEL`: Model to use (default: llama3.1-70b)
- `TEMPERATURE`: Generation temperature (default: 0.0)
- `MAX_TOKENS_RESPONSE`: Max tokens in response (default: 4000)
- `MAX_TOKENS_PER_CHUNK`: Max tokens per chunk for map-reduce (default: 50000)

### Configuration Class

All configuration is centralized in `src/config.py`. To add new settings:

1. Add environment variable to `.env.example`
2. Add field to `Config` class
3. Update validation if required

## Adding Features

### Adding a New LLM Provider

1. Create new client class similar to `CerebrasClient`
2. Implement `generate_digest()` and `generate_digest_map_reduce()` methods
3. Update `DigestGenerator` to support provider selection

### Adding New Output Formats

1. Add method to `OutputHandler` class
2. Update CLI arguments in `main.py`
3. Add documentation

### Customizing Prompts

Edit prompts in `CerebrasClient`:
- `_get_default_system_prompt()`: System instructions
- `_create_user_prompt()`: User message format
- `_create_reduce_prompt()`: Map-reduce combination prompt

## Testing

### Manual Testing

```bash
# Test with small dataset
python -m src.main \
  --channels @test_channel \
  --start-date 2025-10-04 \
  --end-date 2025-10-05

# Test file output
python -m src.main \
  --channels @test_channel \
  --output-file test_digest.txt

# Test Telegram send
python -m src.main \
  --channels @test_channel \
  --send-to-telegram \
  --telegram-target @test_output
```

### Unit Tests (Future)

Recommended structure:
```
tests/
├── test_telegram_fetcher.py
├── test_cerebras_client.py
├── test_digest_generator.py
└── test_output_handler.py
```

## Code Style

- Follow PEP 8
- Use type hints
- Add docstrings to all public functions/classes
- Keep functions focused and small
- Use async/await for I/O operations

## Error Handling

- Use try-except blocks for external API calls
- Provide informative error messages
- Log errors with context
- Fail gracefully when possible

## Performance Considerations

### Message Fetching
- Uses `iter_messages()` for memory efficiency
- Breaks early when date range exceeded

### LLM Processing
- Estimates tokens to decide on single-pass vs map-reduce
- Splits on message boundaries to preserve context

### Rate Limiting
- Respects Telegram API limits
- Cerebras API has generous limits (verify your plan)

## Security

### Sensitive Data
- Never commit `.env` files
- Keep session files private (`*.session`)
- Don't log API keys or tokens

### Best Practices
- Validate user input
- Sanitize channel names
- Use environment variables for secrets

## Future Improvements

### Short-term
- [ ] Add unit tests
- [ ] Add logging framework
- [ ] Improve error messages
- [ ] Add progress bars

### Medium-term
- [ ] SQLite database for caching messages
- [ ] Web UI for configuration
- [ ] Support for private channels
- [ ] Custom category configuration

### Long-term
- [ ] Multi-user support
- [ ] Scheduled digest generation
- [ ] Analytics and statistics
- [ ] Docker deployment

## Contributing

When contributing:
1. Follow the existing code style
2. Add docstrings to new functions
3. Update documentation
4. Test thoroughly
5. Keep commits focused

## Debugging

### Enable verbose output
Set in `config.py` or add debug flag:
```python
import logging
logging.basicConfig(level=logging.DEBUG)
```

### Common issues
- Session file corruption: Delete `*.session` files
- API rate limits: Wait before retrying
- Large memory usage: Reduce date range or use map-reduce

## Resources

- [Telethon Documentation](https://docs.telethon.dev/)
- [Cerebras API Reference](https://inference-docs.cerebras.ai/)
- [Python asyncio](https://docs.python.org/3/library/asyncio.html)
