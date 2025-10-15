# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

## [0.6.0] - 2025-10-13

### Added
- **🐳 Docker support** - Complete containerization for easy VPS deployment
- Dockerfile with Python 3.11 and all dependencies
- docker-compose.yml with proper volume mounts for persistence
- docker-run.sh script for easy container execution
- Logging to files (logs/digest.log) in addition to console
- .dockerignore for optimized build context

### Documentation
- DOCKER_DEPLOYMENT.md - Complete VPS deployment guide
- VPS_QUICKSTART.md - Quick start guide for fast deployment
- DOCKER.md - Docker files overview and troubleshooting
- vps-cron.sh.example - Template for VPS cron scheduling

### Improved
- Persistent storage for sessions, logs, and output via Docker volumes
- Easy updates via rebuild (git pull + docker-compose build)
- Isolated environment eliminates dependency conflicts
- Better logging with file output for debugging

### Infrastructure
- Added logging configuration in main.py
- Created logs/ directory structure
- Session files now stored in sessions/ directory
- Output digests stored in output/ directory

## [0.5.0] - 2025-10-07

### Added
- **Telegram folder invite link support** - Automatically expand folder links to channel lists
- `extract_folder_slug()` method to parse `t.me/addlist/` URLs
- `get_channels_from_folder()` method to resolve folders via Telethon API
- `has_folder_links()` helper in Config to detect folder URLs
- Support for both `ChatlistInvite` and `ChatlistInviteAlready` response types
- Folder links work in `channels.yaml`, CLI arguments, and channel groups

### Improved
- Automatic duplicate removal when expanding multiple folder links
- Clear console feedback when expanding folders (channel count and names)
- Error handling for invalid folder URLs or access issues
- Support for mixing regular channels and folder links

### Documentation
- Updated `channels.yaml.example` with folder link examples
- Added folder link usage to README.md
- Documented folder link feature in Copilot instructions

## [0.4.0] - 2025-10-07

### Changed
- **BREAKING**: Switched to Bot API only for Telegram sending (removed Telethon sending)
- **BREAKING**: Changed from MarkdownV2 to HTML formatting for better reliability
- **BREAKING**: Removed `--use-bot` CLI argument (Bot API is now the only option)
- Digest format: category → emoji + bold headline → optional quote → links
- Categories and news items now sorted by importance

### Added
- Smart Markdown to HTML converter for Telegram Bot API
- Importance-based sorting for categories and news items
- News headline structure with 🔹 emoji
- Optional detailed summaries as `<blockquote>`

### Removed
- Legacy Telethon sending methods (`_send_via_bot`, `_send_via_user_client`)
- Complex MarkdownV2 escaping logic
- `--use-bot` CLI parameter

### Improved
- Simpler, more reliable message sending via HTTP
- Better formatting with HTML (bold, links, blockquotes)
- Fewer escaping edge cases
- Disabled link previews for cleaner appearance

## [0.3.2] - 2025-10-06

### Added
- Clickable hyperlinks for post titles: **[Title](url)**
- 📝 emoji marker for category summaries in *italic*
- Automatic language matching for category names

### Changed
- Removed ━━━━━━━━━━ separators between categories
- Post titles now clickable hyperlinks instead of plain text
- Category summaries in *italic* with 📝 for visual separation
- Source attribution in *italic* for better readability
- Category names auto-detected in same language as posts

### Improved
- Cleaner, more modern appearance
- Better navigation with clickable titles
- Clear visual hierarchy (summary vs posts)
- Proper localization of category names

## [0.3.1] - 2025-10-06

### Added
- Markdown formatting support for digests (bold, links, numbered lists)
- Hidden URLs in markdown links for cleaner text
- Numbered posts within categories (1., 2., 3.)
- Better source attribution format

### Changed
- **BREAKING**: Digest format now uses Markdown instead of plain text
- LLM now generates digest title directly (removed duplicate headers)
- Removed `_generate_header()` method from DigestGenerator
- Updated all prompts to use Markdown formatting
- Category names now use **bold** for better hierarchy
- Links are now hidden in text instead of showing raw URLs

### Improved
- Much better readability in Telegram
- Professional, clean appearance
- Proper text hierarchy with bold headers
- More compact format (hidden URLs)

## [0.3.0] - 2025-10-06

### Added
- **YAML configuration for channels** (`channels.yaml`)
- Support for channel groups (e.g., news, research, education)
- `--config` CLI argument to specify custom config file
- `--group` CLI argument to load specific channel group
- Configuration priority: CLI args > YAML config > environment variables
- `channels.yaml.example` with documented structure
- PyYAML dependency for config parsing

### Changed
- Channel loading now supports three sources with priority order
- Improved CLI help with YAML configuration examples
- Updated README with YAML configuration instructions

### Improved
- More flexible channel management
- Better organization for multiple channel sets
- Easier onboarding with example config file

## [0.2.0] - 2025-10-06

### Added
- Dynamic category generation based on post content analysis
- AI-powered category identification (3-7 categories per digest)
- Flexible emoji selection matching category themes
- Guidelines for natural category emergence

### Changed
- **BREAKING**: Removed hardcoded categories (Research, Tools, News, Tutorials, Other)
- **Default date range**: Now defaults to "today" instead of "yesterday"
- System prompts now emphasize content-based categorization
- Reduce phase intelligently merges similar topics across chunks
- Categories now adapt to actual content rather than forcing predefined templates

### Improved
- Better relevance of digest organization
- More flexible handling of diverse content themes
- Enhanced readability with dynamic category names
- More intuitive default behavior (today's posts instead of yesterday's)

## [0.1.1] - 2025-10-05

### Added
- Telegram-optimized output format (plain text, no Markdown)
- Detailed formatting instructions in system prompts
- Example structure with separators and proper emoji usage

### Changed
- Updated all LLM prompts to avoid Markdown formatting
- Links now displayed on separate lines with 🔗 emoji
- Bullets use • instead of Markdown symbols

### Fixed
- Markdown rendering issues in Telegram messages

## [0.1.0] - 2025-10-05

### Added
- Initial release with core functionality
- Telegram message fetching via Telethon
- Cerebras AI integration for digest generation
- Map-reduce support for large datasets
- CLI interface with comprehensive arguments
- File output and Telegram sending capabilities
- Complete documentation (README, QUICKSTART, DEVELOPMENT, ARCHITECTURE)

### Features
- Multi-channel support
- Date range filtering
- Automatic chunking for large volumes
- Error handling and validation
- Environment-based configuration
- MIT License

---

## Version History

- **0.2.0**: Dynamic category generation
- **0.1.1**: Telegram format optimization
- **0.1.0**: Initial release
