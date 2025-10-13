# VPS Quick Setup Guide

Fast deployment on a fresh VPS (Ubuntu/Debian).

## 1. Prepare VPS

```bash
# Update system
sudo apt update && sudo apt upgrade -y

# Install Docker
curl -fsSL https://get.docker.com -o get-docker.sh
sudo sh get-docker.sh
sudo usermod -aG docker $USER

# Install Docker Compose
sudo apt install docker-compose -y

# Logout and login again for docker group to take effect
exit
```

## 2. Deploy Application

```bash
# SSH back into VPS
ssh user@your-vps-ip

# Clone repository
git clone https://github.com/sserov/telegram-digest.git
cd telegram-digest

# Configure credentials
cp .env.example .env
nano .env  # Add your API keys

# Configure channels
cp channels.yaml.example channels.yaml
nano channels.yaml  # Add your channels

# Build Docker image
docker-compose build

# First run - authenticate with Telegram
docker-compose run --rm telegram-digest python -m src.main --channels @test_channel
# Enter phone number and code when prompted

# Test run
./docker-run.sh

# Check output
ls -la output/
cat output/digest_*.txt
```

## 3. Schedule with Cron

```bash
# Get full path
pwd  # Copy this path

# Edit crontab
crontab -e

# Add this line (replace /full/path with your actual path):
0 22 * * * cd /full/path/telegram-digest && ./docker-run.sh >> logs/cron.log 2>&1

# Save and exit (Ctrl+X, then Y, then Enter)

# Verify
crontab -l
```

## 4. Monitor

```bash
# Watch logs in real-time
tail -f logs/cron.log

# Check digests
ls -la output/

# Check last run
cat output/digest_*.txt | tail -n 50
```

## 5. Update

```bash
cd telegram-digest
git pull
docker-compose build
./docker-run.sh  # Test
# Done! Cron will use new version
```

## Troubleshooting

```bash
# Check if Docker is running
docker ps

# Check container logs
docker-compose logs --tail=50

# Test manually
./docker-run.sh

# Rebuild from scratch
docker-compose down
docker system prune -a -f
docker-compose build --no-cache
```

## Security Checklist

- ✅ Set up SSH keys (no password login)
- ✅ Configure firewall: `sudo ufw allow 22 && sudo ufw enable`
- ✅ Protect .env: `chmod 600 .env`
- ✅ Regular updates: `sudo apt update && sudo apt upgrade`

That's it! Your digest will run daily at 22:00 UTC.

For detailed documentation, see [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md).
