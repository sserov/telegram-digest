#!/usr/bin/env bash
# Quick runner script for Telegram Digest

set -e

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

echo "======================================"
echo "   Telegram Digest - Quick Runner"
echo "======================================"
echo ""

# Check if virtual environment is activated
if [[ -z "${VIRTUAL_ENV}" ]]; then
    echo -e "${YELLOW}Warning: Virtual environment not activated${NC}"
    echo "Run: source venv/bin/activate"
    echo ""
    read -p "Continue anyway? (y/n) " -n 1 -r
    echo
    if [[ ! $REPLY =~ ^[Yy]$ ]]; then
        exit 1
    fi
fi

# Check if .env exists
if [ ! -f .env ]; then
    echo -e "${RED}Error: .env file not found${NC}"
    echo "Run: cp .env.example .env"
    echo "Then edit .env with your credentials"
    exit 1
fi

# Default values
CHANNELS=""
START_DATE=$(date -v-1d '+%Y-%m-%d' 2>/dev/null || date -d "yesterday" '+%Y-%m-%d')
END_DATE=$(date '+%Y-%m-%d')
OUTPUT_FILE=""
SEND_TO_TG="false"
TG_TARGET=""

# Parse arguments
while [[ $# -gt 0 ]]; do
    case $1 in
        -c|--channels)
            CHANNELS="$2"
            shift 2
            ;;
        -s|--start-date)
            START_DATE="$2"
            shift 2
            ;;
        -e|--end-date)
            END_DATE="$2"
            shift 2
            ;;
        -o|--output-file)
            OUTPUT_FILE="$2"
            shift 2
            ;;
        --send)
            SEND_TO_TG="true"
            shift
            ;;
        --target)
            TG_TARGET="$2"
            shift 2
            ;;
        -h|--help)
            echo "Usage: ./run.sh [OPTIONS]"
            echo ""
            echo "Options:"
            echo "  -c, --channels CHANNELS      Telegram channels (e.g., '@ai_news @ml_research')"
            echo "  -s, --start-date DATE        Start date (YYYY-MM-DD, default: yesterday)"
            echo "  -e, --end-date DATE          End date (YYYY-MM-DD, default: today)"
            echo "  -o, --output-file FILE       Output file path"
            echo "  --send                       Send to Telegram"
            echo "  --target CHANNEL             Telegram target channel"
            echo "  -h, --help                   Show this help"
            echo ""
            echo "Examples:"
            echo "  ./run.sh -c '@ai_news @ml_research'"
            echo "  ./run.sh -c '@ai_news' -s 2025-10-01 -e 2025-10-03"
            echo "  ./run.sh -c '@ai_news' --send --target @my_channel"
            exit 0
            ;;
        *)
            echo -e "${RED}Unknown option: $1${NC}"
            echo "Use -h or --help for usage information"
            exit 1
            ;;
    esac
done

# Check if channels provided
if [ -z "$CHANNELS" ]; then
    echo -e "${YELLOW}No channels specified. Using interactive mode.${NC}"
    echo ""
    read -p "Enter channel(s) (e.g., @ai_news @ml_research): " CHANNELS
    if [ -z "$CHANNELS" ]; then
        echo -e "${RED}Error: No channels provided${NC}"
        exit 1
    fi
fi

# Build command
CMD="python -m src.main --channels $CHANNELS --start-date $START_DATE --end-date $END_DATE"

if [ -n "$OUTPUT_FILE" ]; then
    CMD="$CMD --output-file $OUTPUT_FILE"
fi

if [ "$SEND_TO_TG" = "true" ]; then
    CMD="$CMD --send-to-telegram"
    if [ -n "$TG_TARGET" ]; then
        CMD="$CMD --telegram-target $TG_TARGET"
    fi
fi

echo ""
echo "Configuration:"
echo "  Channels: $CHANNELS"
echo "  Date range: $START_DATE to $END_DATE"
if [ -n "$OUTPUT_FILE" ]; then
    echo "  Output file: $OUTPUT_FILE"
fi
if [ "$SEND_TO_TG" = "true" ]; then
    echo "  Send to Telegram: Yes"
    if [ -n "$TG_TARGET" ]; then
        echo "  Target: $TG_TARGET"
    fi
fi
echo ""

# Execute
echo -e "${GREEN}Running digest generator...${NC}"
echo ""

eval $CMD

echo ""
echo -e "${GREEN}Done!${NC}"
