import os

# Paths
BASE_DIR = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
DATABASE_DIR = os.path.join(BASE_DIR, "database")
LOG_DIR = os.path.join(BASE_DIR, "logs")

GUILD_SETTINGS_FILE = os.path.join(DATABASE_DIR, "guild_settings.json")
POSTED_GAMES_FILE = os.path.join(DATABASE_DIR, "posted_games.json")
STATE_FILE = os.path.join(DATABASE_DIR, "state.json")

# URLs
RSS_URL = "https://online-fix.me/rss.xml"

# Colors (Clean, professional, dark theme appropriate)
EMBED_COLOR = 0x2B2D31  # Discord's dark theme embed color
SUCCESS_COLOR = 0x57F287
ERROR_COLOR = 0xED4245
WARNING_COLOR = 0xFEE75C

# Network
HTTP_TIMEOUT = 15
HTTP_RETRIES = [1, 5, 15, 30]

# Assets
ASSETS_DIR = os.path.join(BASE_DIR, "assets")
LOGO_PATH = os.path.join(ASSETS_DIR, "onlinefix_logo.png")
LOGO_FILENAME = "onlinefix_logo.png"
