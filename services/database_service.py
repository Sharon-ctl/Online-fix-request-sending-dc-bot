import json
import os
import shutil
from typing import Dict, Any, Optional
from utils.constants import GUILD_SETTINGS_FILE, POSTED_GAMES_FILE, STATE_FILE, DATABASE_DIR
from utils.logger import log
from utils.exceptions import DatabaseError

class DatabaseService:
    def __init__(self):
        self._ensure_dir()
        
        self.guild_settings = self._load_json(GUILD_SETTINGS_FILE, {})
        self.posted_games = self._load_json(POSTED_GAMES_FILE, {})
        self.state = self._load_json(STATE_FILE, {
            "last_fetch": "",
            "rss_etag": "",
            "rss_modified": ""
        })

    def _ensure_dir(self):
        if not os.path.exists(DATABASE_DIR):
            os.makedirs(DATABASE_DIR)
            log.info(f"Created database directory at {DATABASE_DIR}")

    def _load_json(self, filepath: str, default: Any) -> Any:
        if not os.path.exists(filepath):
            self._save_json(filepath, default)
            return default

        try:
            with open(filepath, "r", encoding="utf-8") as f:
                return json.load(f)
        except json.JSONDecodeError:
            log.error(f"action=db_corrupted file={filepath}")
            corrupted_path = filepath + ".corrupt"
            shutil.move(filepath, corrupted_path)
            log.info(f"Moved corrupted file to {corrupted_path}")
            self._save_json(filepath, default)
            return default
        except Exception as e:
            raise DatabaseError(f"Failed to read database file {filepath}: {e}")

    def _save_json(self, filepath: str, data: Any) -> None:
        try:
            with open(filepath, "w", encoding="utf-8") as f:
                json.dump(data, f, indent=4, ensure_ascii=False)
        except Exception as e:
            raise DatabaseError(f"Failed to write to database file {filepath}: {e}")

    # --- Guild Settings ---
    
    def get_guild_channel(self, guild_id: int) -> Optional[int]:
        guild_data = self.guild_settings.get(str(guild_id))
        if guild_data and "channel_id" in guild_data:
            return int(guild_data["channel_id"])
        return None

    def set_guild_channel(self, guild_id: int, channel_id: int) -> None:
        self.guild_settings[str(guild_id)] = {"channel_id": str(channel_id)}
        self._save_json(GUILD_SETTINGS_FILE, self.guild_settings)
        
    def remove_guild(self, guild_id: int) -> None:
        if str(guild_id) in self.guild_settings:
            del self.guild_settings[str(guild_id)]
            self._save_json(GUILD_SETTINGS_FILE, self.guild_settings)

    def get_all_guilds(self) -> Dict[str, Dict[str, str]]:
        return self.guild_settings

    # --- Posted Games ---
    
    def is_game_posted(self, guid: str) -> bool:
        return guid in self.posted_games

    def mark_game_posted(self, guid: str, title: str, timestamp: str) -> None:
        self.posted_games[guid] = {
            "title": title,
            "posted_at": timestamp
        }
        
        # Memory / Disk Leak fix: Cap the dictionary size to prevent infinite growth (keep last 1000)
        if len(self.posted_games) > 1000:
            # Dictionaries maintain insertion order in modern Python, oldest are at the top
            keys_to_remove = list(self.posted_games.keys())[:-1000]
            for k in keys_to_remove:
                del self.posted_games[k]
                
        self._save_json(POSTED_GAMES_FILE, self.posted_games)

    # --- State ---
    
    def get_state(self) -> Dict[str, str]:
        return self.state
        
    def update_state(self, key: str, value: str) -> None:
        self.state[key] = value
        self._save_json(STATE_FILE, self.state)
