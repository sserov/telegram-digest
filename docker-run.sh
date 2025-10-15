#!/bin/bash

# Telegram Digest - Docker Runner Script
# This script runs the digest generation in Docker container

set -e

# Navigate to script directory
SCRIPT_DIR="$(cd "$(dirname "${BASH_SOURCE[0]}")" && pwd)"
cd "$SCRIPT_DIR"

# Detect Docker Compose command (v2: 'docker compose', v1: 'docker-compose')
if docker compose version &> /dev/null; then
    DOCKER_COMPOSE="docker compose"
elif docker-compose version &> /dev/null; then
    DOCKER_COMPOSE="docker-compose"
else
    echo "❌ Error: Docker Compose not found"
    echo "   Install Docker Compose: https://docs.docker.com/compose/install/"
    exit 1
fi

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
    echo "📱 Starting interactive authentication..."
    echo "   You will need to enter your phone number and confirmation code."
    echo ""
    
    # Run interactive authentication
    $DOCKER_COMPOSE run --rm telegram-digest python -m src.main --channels @test_channel
    
    # Check if session was created
    if [ ! -f sessions/telegram_session.session ]; then
        echo ""
        echo "❌ Authentication failed - session file not created"
        echo "   Please try again and make sure to:"
        echo "   1. Enter your phone number with country code (e.g., +1234567890)"
        echo "   2. Wait for the code in Telegram"
        echo "   3. Enter the confirmation code"
        exit 1
    fi
    
    echo ""
    echo "✅ Authentication successful! Session saved."
    echo "   Now starting digest generation..."
    echo ""
fi

# Run digest generation
echo "🚀 Starting Telegram Digest Generator..."
$DOCKER_COMPOSE up --abort-on-container-exit

# Get exit code
EXIT_CODE=$?

if [ $EXIT_CODE -eq 0 ]; then
    echo "✅ Digest generated successfully"
else
    echo "❌ Digest generation failed with exit code $EXIT_CODE"
    echo "   Check logs/digest.log for details"
fi

# Cleanup
$DOCKER_COMPOSE down

exit $EXIT_CODE
