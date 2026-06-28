# Online-Fix Tracker

A production-grade Python Discord bot that monitors the `https://online-fix.me/rss.xml` feed and automatically posts newly released games into configured Discord channels.

## Features
- **Modern UI**: Uses Discord Components V2 (Embeds & Buttons) with no emojis.
- **Robust Parsing**: Extracts relevant details directly from the HTML description of the RSS feed.
- **Data Safety**: Automatic `.corrupt` database recovery for JSON files.
- **Multi-Guild**: Fetches RSS once and distributes to all configured guilds.
- **Configurable**: Define the polling interval in minutes via environment variables.
- **Graceful Shutdown**: Properly closes network sessions and scheduler upon exit.

## Setup Requirements
- Python 3.13+
- Discord Bot Token
- Bot Owner ID (for admin commands and notifications)

## Installation (Native)

1. Clone the repository.
2. Install dependencies:
   ```bash
   pip install -r requirements.txt
   ```
3. Copy `.env.example` to `.env` and fill in the values:
   ```env
   BOT_TOKEN=your_bot_token_here
   OWNER_ID=your_owner_id_here
   FETCH_INTERVAL_MINUTES=5
   LOG_LEVEL=INFO
   ```
4. Run the bot:
   ```bash
   python launcher.py
   ```

## Installation (Docker)

Using `docker-compose` is highly recommended.

1. Create and populate `.env` as shown above.
2. Build and start the container:
   ```bash
   docker-compose up -d --build
   ```

## Commands

### User Commands
- `!channel set <#channel>`: Configure the channel for the bot to post releases. Requires **Manage Server** permission.
- `!help`: Display help information.

### Owner Commands
- `!test`: Run an end-to-end test (fetches RSS, grabs newest release, sends a preview without altering the DB).
- `!fetch`: Instantly force an RSS check and post any new releases.
- `!health`: Show bot uptime, memory usage, and scheduler status.
- `!reload`: Reload database configuration.

## Systemd Service Example

If running directly on Linux without Docker, you can create a systemd service:

`/etc/systemd/system/onlinefix.service`
```ini
[Unit]
Description=Online-Fix Tracker Bot
After=network.target

[Service]
Type=simple
User=your_user
WorkingDirectory=/path/to/onlinefix-bot
ExecStart=/path/to/onlinefix-bot/venv/bin/python launcher.py
Restart=on-failure
RestartSec=5s

[Install]
WantedBy=multi-user.target
```

Enable and start:
```bash
sudo systemctl enable onlinefix
sudo systemctl start onlinefix
```
