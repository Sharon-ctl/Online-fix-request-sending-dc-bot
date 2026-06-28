import logging
import sys
import os
from logging.handlers import RotatingFileHandler
from utils.constants import LOG_DIR
from config import Config

def setup_logger(name: str = "bot") -> logging.Logger:
    """Sets up and returns a configured logger."""
    
    if not os.path.exists(LOG_DIR):
        os.makedirs(LOG_DIR)
        
    logger = logging.getLogger(name)
    
    # Avoid adding multiple handlers if setup is called multiple times
    if logger.handlers:
        return logger
        
    level = getattr(logging, Config.LOG_LEVEL.upper(), logging.INFO)
    logger.setLevel(level)

    # Formatter for structured logs
    formatter = logging.Formatter(
        fmt="[%(levelname)s] %(asctime)s - %(name)s - %(message)s",
        datefmt="%Y-%m-%d %H:%M:%S"
    )

    # Console Handler
    console_handler = logging.StreamHandler(sys.stdout)
    console_handler.setFormatter(formatter)
    
    # File Handler (10MB max size, 5 backups)
    log_file = os.path.join(LOG_DIR, "bot.log")
    file_handler = RotatingFileHandler(
        filename=log_file,
        maxBytes=10 * 1024 * 1024,  # 10 MB
        backupCount=5,
        encoding="utf-8"
    )
    file_handler.setFormatter(formatter)

    logger.addHandler(console_handler)
    logger.addHandler(file_handler)
    
    # Also capture discord.py logs
    discord_logger = logging.getLogger("discord")
    discord_logger.setLevel(level)
    
    # Suppress voice warnings
    class VoiceWarningFilter(logging.Filter):
        def filter(self, record):
            return "voice will NOT be supported" not in record.getMessage()
            
    discord_logger.addFilter(VoiceWarningFilter())
    
    discord_logger.addHandler(console_handler)
    discord_logger.addHandler(file_handler)

    return logger

log = setup_logger()
