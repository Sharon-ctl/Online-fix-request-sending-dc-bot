import os
from typing import Optional
from dotenv import load_dotenv
from utils.exceptions import ConfigurationError

load_dotenv()

class Config:
    BOT_TOKEN: str = os.getenv("BOT_TOKEN", "")
    OWNER_ID: Optional[int] = None
    FETCH_INTERVAL_MINUTES: int = int(os.getenv("FETCH_INTERVAL_MINUTES", "5"))
    LOG_LEVEL: str = os.getenv("LOG_LEVEL", "INFO")

    @classmethod
    def validate(cls) -> None:
        if not cls.BOT_TOKEN:
            raise ConfigurationError("BOT_TOKEN is missing or empty in environment variables.")
        
        owner_id_raw = os.getenv("OWNER_ID")
        if not owner_id_raw:
            raise ConfigurationError("OWNER_ID is missing or empty in environment variables.")
        try:
            cls.OWNER_ID = int(owner_id_raw)
        except ValueError:
            raise ConfigurationError(f"OWNER_ID must be a valid integer, got: {owner_id_raw}")
        
        if cls.FETCH_INTERVAL_MINUTES < 1:
            raise ConfigurationError("FETCH_INTERVAL_MINUTES must be at least 1.")
