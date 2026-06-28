class OnlineFixError(Exception):
    """Base exception class for Online-Fix Tracker bot."""
    pass

class ConfigurationError(OnlineFixError):
    """Raised when there is an issue with the bot's configuration."""
    pass

class RSSFetchError(OnlineFixError):
    """Raised when the RSS feed cannot be fetched."""
    pass

class RSSParseError(OnlineFixError):
    """Raised when the RSS feed cannot be parsed correctly."""
    pass

class DatabaseError(OnlineFixError):
    """Raised when there is an issue reading from or writing to the database."""
    pass

class DiscordPostError(OnlineFixError):
    """Raised when the bot fails to post a message to Discord."""
    pass

class PermissionError(OnlineFixError):
    """Raised when the bot lacks necessary permissions."""
    pass

class ChannelNotConfigured(OnlineFixError):
    """Raised when a guild has no channel configured for releases."""
    pass
