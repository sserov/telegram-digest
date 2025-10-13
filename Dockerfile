# Telegram Digest Generator - Docker Image
FROM python:3.13-slim

# Set working directory
WORKDIR /app

# Install system dependencies needed for Python packages
# gcc: Required for building cryptography package (used by Telethon)
RUN apt-get update && apt-get install -y \
    gcc \
    && rm -rf /var/lib/apt/lists/*

# Copy requirements first (for better Docker layer caching)
COPY requirements.txt .

# Install Python dependencies
RUN pip install --no-cache-dir -r requirements.txt

# Copy application code
COPY src/ ./src/

# Create directories for mounted volumes (optional, volumes will override)
RUN mkdir -p /app/logs /app/sessions /app/output

# Set environment variables
ENV PYTHONUNBUFFERED=1

# Default command
CMD ["python", "-m", "src.main", "--send-to-telegram"]
