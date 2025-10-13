#!/bin/bash

# Telegram Digest - Docker Runner Script
# This script runs the digest generation in Docker container

set -e

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Check if .env exists
if [ ! -f .env ]; then
    echo "❌ Error: .env file not found"
    echo "   Please create .env file with your credentials"
    echo "   See .env.example for reference"
    exit 1
fi

# Check if channels.yaml exists
if [ ! -f channels.yaml ]; then
    echo "⚠️  Warning: channels.yaml not found"
    echo "   Creating from example..."
    cp channels.yaml.example channels.yaml
    echo "   Please edit channels.yaml with your channels"
fi

# Create necessary directories
mkdir -p logs sessions output

# Check if Telegram session exists
if [ ! -f sessions/telegram_session.session ]; then
    echo "⚠️  Warning: Telegram session not found"
    echo ""
    echo "First-time setup required:"
    echo "Run this command for interactive authentication:"
    echo ""
    echo "  docker-compose run --rm telegram-digest python -m src.main --channels @test_channel"
    echo ""
    echo "After authentication, run this script again."
    exit 1
fi

# Run digest generation
echo "🚀 Starting Telegram Digest Generator..."
docker-compose up --abort-on-container-exit

# Get exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Digest generated successfully"
else
    echo "❌ Digest generation failed with exit code $EXIT_CODE"
    echo "   Check logs/digest.log for details"
fi

# Cleanup
docker-compose down

exit $EXIT_CODE
