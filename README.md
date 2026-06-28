# Online-Fix Tracker

A production-grade Python Discord bot that monitors the `https://online-fix.me/rss.xml` feed and automatically posts newly released games into configured Discord channels.

## Features
- **Auto-Translations**: Real-time Russian-to-English translation using `googletrans` API.
- **Cloudflare Bypass**: Embedded `curl_cffi` to evade advanced Web Application Firewalls natively.
- **Interactive UI**: Gorgeous layout built on native Discord Components V2 framework.
- **Smart Pagination**: Lazily loads and translates pages for commands with massive outputs to optimize performance and prevent rate limiting.

## Available Commands

- `!ping` - Check the bot latency.
- `!help` - Display the help menu.
- `!set <#channel>` - (Admin Only) Set the notification channel.
- `!search <query>` - Find specific games with smart pagination handling up to 50 results.
- `!updates` - View the 50 most recent game updates released on the site.
- `!trending` - Directly checks the hottest and most popular games being played right now.
- `!genre [genre]` - Browse games by a specific category (e.g. `!genre shooter`, `!genre rpg`).

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

## Commands

### User Commands
- `!search <query>`: Search the Online-Fix database for a specific game. Automatically translates and renders the top 10 results.
- `!help`: Display help information.

### Admin Commands
- `!channel set <#channel>`: Configure the channel for the bot to post automated releases. Requires **Manage Server** permission.

### Owner Commands
- `!ping`: Check the WebSocket latency of the bot.
- `!test`: Run an end-to-end test (fetches RSS, grabs newest release, translates it, and sends a preview).
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
