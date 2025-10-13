# Docker Files Overview

This directory contains Docker-related files for deploying Telegram Digest Generator in containers.

## Files

### Core Files
- **Dockerfile** - Image definition with Python 3.11 and dependencies
- **docker-compose.yml** - Service configuration with volume mounts
- **.dockerignore** - Files to exclude from Docker build context

### Scripts
- **docker-run.sh** - Run digest generation in Docker (for manual testing)
- **vps-cron.sh.example** - Template for VPS cron execution

### Documentation
- **DOCKER_DEPLOYMENT.md** - Complete deployment guide for VPS
- **VPS_QUICKSTART.md** - Quick start guide for fast deployment

## Quick Reference

### Build Image
```bash
docker-compose build
```

### Run Once
```bash
./docker-run.sh
```

### Update Application
```bash
git pull
docker-compose build
```

### View Logs
```bash
docker-compose logs
# or
cat logs/digest.log
```

## Volume Mounts

The following directories are mounted as volumes (persistent storage):

- `./channels.yaml` → `/app/channels.yaml` - Your channel configuration
- `./sessions/` → `/app/sessions/` - Telegram authentication sessions
- `./logs/` → `/app/logs/` - Application logs
- `./output/` → `/app/output/` - Generated digests

These files persist between container runs and updates.

## Environment Variables

Loaded from `.env` file:
- `TELEGRAM_API_ID`
- `TELEGRAM_API_HASH`
- `CEREBRAS_API_KEY`
- `TELEGRAM_BOT_TOKEN`
- `OUTPUT_TELEGRAM_CHANNEL`

See `.env.example` for all available variables.

## Ports

No ports are exposed - this is a scheduled batch job, not a server.

## Resource Usage

Typical resource consumption:
- **CPU**: Low (only during execution, ~2-5 minutes)
- **Memory**: ~200-500 MB during execution
- **Disk**: ~100 MB for image + logs/sessions
- **Network**: ~1-10 MB per execution (depending on message count)

## Security

- Never commit `.env` file
- Session files are sensitive (Telegram auth) - keep secure
- Run container as non-root user (configured in Dockerfile)
- Use read-only mounts where possible

## Troubleshooting

### Container fails to start
```bash
docker-compose logs
```

### Permission issues
```bash
# Fix permissions on mounted volumes
sudo chown -R $(id -u):$(id -g) sessions/ logs/ output/
```

### Out of disk space
```bash
# Clean up old Docker resources
docker system prune -a
```

### Network issues
```bash
# Check if container can reach internet
docker-compose run --rm telegram-digest ping -c 3 8.8.8.8
```

## See Also

- [DOCKER_DEPLOYMENT.md](DOCKER_DEPLOYMENT.md) - Full deployment guide
- [VPS_QUICKSTART.md](VPS_QUICKSTART.md) - Quick setup for VPS
- [README.md](README.md) - Main documentation
