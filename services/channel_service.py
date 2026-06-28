import discord
import asyncio
from typing import List, Tuple
from utils.logger import log
from utils.exceptions import DiscordPostError
from utils.permissions import validate_bot_channel_permissions
from services.database_service import DatabaseService

class ChannelService:
    def __init__(self, bot: discord.Client, db_service: DatabaseService):
        self.bot = bot
        self.db_service = db_service

    async def broadcast_release(self, view: discord.ui.LayoutView) -> None:
        """Broadcasts a release to all configured guild channels."""
        guild_settings = self.db_service.get_all_guilds()
        
        for guild_id_str, settings in list(guild_settings.items()):
            try:
                guild_id = int(guild_id_str)
                channel_id = int(settings.get("channel_id", 0))
                
                if not channel_id:
                    continue
                    
                guild = self.bot.get_guild(guild_id)
                if not guild:
                    # Bot was removed from guild or guild is unavailable
                    log.warning(f"action=guild_not_found guild={guild_id}")
                    continue
                    
                channel = guild.get_channel(channel_id)
                if not channel:
                    # Channel was deleted
                    log.warning(f"action=channel_not_found guild={guild_id} channel={channel_id}")
                    continue
                
                # Check permissions before sending
                if guild.me:
                    can_send, missing = validate_bot_channel_permissions(channel, guild.me)
                    if not can_send:
                        log.warning(f"action=missing_permissions guild={guild_id} missing={missing}")
                        continue
                
                try:
                    await channel.send(view=view)
                    log.info(f"action=post guild={guild_id} channel={channel_id} success=true")
                except discord.Forbidden:
                    log.warning(f"action=post_forbidden guild={guild_id} channel={channel_id}")
                except discord.HTTPException as e:
                    log.error(f"action=post_failed guild={guild_id} channel={channel_id} error={e}")
                    
                # Rate limit per channel when broadcasting to multiple guilds
                await asyncio.sleep(1)
                    
            except Exception as e:
                log.error(f"action=broadcast_loop_error error={e}")

    async def notify_owner(self, title: str, message: str) -> None:
        """Sends a direct message to the bot owner on critical failures."""
        from config import Config
        from services.component_service import ComponentService
        if not Config.OWNER_ID:
            return
            
        try:
            owner = self.bot.get_user(Config.OWNER_ID)
            if not owner:
                owner = await self.bot.fetch_user(Config.OWNER_ID)
                
            view = ComponentService.create_error_message(title, message)
            await owner.send(view=view)
        except Exception as e:
            log.error(f"action=notify_owner_failed error={e}")
