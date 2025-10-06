# Changelog

All notable changes to this project will be documented in this file.

The format is based on [Keep a Changelog](https://keepachangelog.com/en/1.0.0/),
and this project adheres to [Semantic Versioning](https://semver.org/spec/v2.0.0.html).

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
