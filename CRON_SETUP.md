# Cron Setup for Telegram Digest

## Automated Daily Digest Generation

The project is configured to automatically generate and send digests every day at 22:00 (10 PM).

**⚠️ macOS Users**: Recent macOS versions have strict security policies. If you get "Operation not permitted" errors, you need to grant Full Disk Access to cron (see Troubleshooting section below).

## Setup Details

### Script: `run_digest.sh`

First, create your script from the example:

```bash
cp run_digest.sh.example run_digest.sh
```

Edit `run_digest.sh` and update the `PROJECT_DIR` variable with your actual project path:

```bash
PROJECT_DIR="/Users/yourusername/path/to/telegram-digest"
```

Make the script executable:

```bash
chmod +x run_digest.sh
```

The script:
1. Navigates to project directory
2. Activates Python virtual environment
3. Runs digest generation with `--send-to-telegram` flag
4. Deactivates venv

### Cron Job

Add to crontab (replace paths with your actual paths):

```bash
0 22 * * * /path/to/telegram-digest/run_digest.sh >> /path/to/telegram-digest/cron.log 2>&1
```

**Schedule:** Daily at 22:00 (10 PM)

**Logging:** All output (stdout and stderr) is logged to `cron.log`

## Management Commands

### View Current Cron Jobs
```bash
crontab -l
```

### Edit Cron Jobs
```bash
crontab -e
```

### Remove All Cron Jobs
```bash
crontab -r
```

### Remove Specific Job
```bash
crontab -e
# Delete the line with run_digest.sh and save
```

## View Logs

```bash
tail -f /Users/sserov/Documents/PROJECTS/telegram-digest/cron.log
```

Or view recent logs:
```bash
tail -n 50 /Users/sserov/Documents/PROJECTS/telegram-digest/cron.log
```

## Testing

Test the script manually before relying on cron:

```bash
/Users/sserov/Documents/PROJECTS/telegram-digest/run_digest.sh
```

## Troubleshooting

### macOS: "Operation not permitted" Error

This is the most common issue on macOS Catalina and later.

**Symptoms:**
```
/bin/bash: /path/to/run_digest.sh: Operation not permitted
```

**Solution: Grant Full Disk Access to cron**

1. Open **System Settings** (or System Preferences on older macOS)
2. Go to **Privacy & Security** → **Full Disk Access**
3. Click the lock 🔒 and authenticate with your password
4. Click the `+` button
5. Press `Cmd+Shift+G` to open "Go to folder"
6. Enter `/usr/sbin/cron` and press Enter
7. Select `cron` and click "Open"
8. Enable the checkbox for `cron`
9. Restart your Mac (or just test the cron job)

**Alternative: Check script permissions**
```bash
# Make sure script is executable
chmod +x /path/to/run_digest.sh

# Test manually first
/path/to/run_digest.sh

# Check file permissions
ls -la /path/to/run_digest.sh
```

### Cron Not Running

1. **Check cron service is running (macOS):**
   ```bash
   sudo launchctl list | grep cron
   ```

2. **Grant Full Disk Access to cron:**
   - System Preferences → Security & Privacy → Privacy → Full Disk Access
   - Add `/usr/sbin/cron`

3. **Check cron logs:**
   ```bash
   log show --predicate 'process == "cron"' --last 1h
   ```

### Script Fails in Cron

1. **Use absolute paths** - Already configured in `run_digest.sh`
2. **Check environment variables** - Ensure `.env` file exists and is readable
3. **Verify PROJECT_DIR** - Make sure the path in `run_digest.sh` is correct
4. **Check permissions:**
   ```bash
   ls -la run_digest.sh
   ```

### No Digest Sent

1. **Check logs:**
   ```bash
   cat cron.log
   ```

2. **Verify Telegram bot token:**
   ```bash
   grep TELEGRAM_BOT_TOKEN .env
   ```

3. **Check OUTPUT_TELEGRAM_CHANNEL in .env**

4. **Test manually:**
   ```bash
   ./run_digest.sh
   # or
   python -m src.main --send-to-telegram
   ```

## Changing Schedule

To change the execution time, edit crontab:

```bash
crontab -e
```

Cron format:
```
* * * * * command
│ │ │ │ │
│ │ │ │ └─── Day of week (0-7, Sunday = 0 or 7)
│ │ │ └───── Month (1-12)
│ │ └─────── Day of month (1-31)
│ └───────── Hour (0-23)
└─────────── Minute (0-59)
```

Examples:
- `0 9 * * *` - Every day at 9:00 AM
- `0 22 * * *` - Every day at 10:00 PM (current)
- `0 18 * * 1-5` - Weekdays at 6:00 PM
- `0 12 * * 0` - Every Sunday at noon
