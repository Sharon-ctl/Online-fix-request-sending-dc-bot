import discord
from discord.ext import commands
import asyncio
from typing import List
from utils.logger import log
from services.database_service import DatabaseService
from services.rss_service import RSSService
from services.channel_service import ChannelService
from services.component_service import ComponentService
from services.release_service import ReleaseService
from services.scheduler_service import SchedulerService
from services.translation_service import TranslationService
from config import Config

class OnlineFixBot(commands.Bot):
    def __init__(self):
        intents = discord.Intents.default()
        intents.message_content = True
        
        super().__init__(
            command_prefix="!",
            intents=intents,
            help_command=None,  # We use our custom help cog
            max_messages=None   # Disable message cache to prevent memory leak over 24/7 runtime
        )
        
        # Initialize Services
        self.db_service = DatabaseService()
        self.rss_service = RSSService(self.db_service)
        self.channel_service = ChannelService(self, self.db_service)
        self.component_service = ComponentService()
        self.translation_service = TranslationService()
        self.release_service = ReleaseService(
            self.rss_service, 
            self.db_service, 
            self.channel_service, 
            self.component_service,
            self.translation_service
        )
        self.scheduler_service = SchedulerService(self.release_service)

    async def setup_hook(self) -> None:
        """Called once when the bot starts up, before login."""
        log.info("action=setup_hook msg=Loading cogs")
        for cog in ["cogs.admin", "cogs.help", "cogs.releases", "cogs.search", "cogs.updates"]:
            try:
                await self.load_extension(cog)
                log.info(f"action=cog_loaded cog={cog}")
            except Exception as e:
                log.error(f"action=cog_load_failed cog={cog} error={e}")

        # Start background tasks
        await self.rss_service.initialize()
        self.scheduler_service.start()

    async def on_ready(self):
        log.info(f"action=bot_ready user={self.user} guilds={len(self.guilds)}")
        await self.change_presence(activity=discord.Activity(type=discord.ActivityType.watching, name="Online-Fix.me"))

    async def on_guild_remove(self, guild: discord.Guild):
        """Cleanup configuration if bot leaves a guild."""
        log.info(f"action=guild_remove guild={guild.id}")
        self.db_service.remove_guild(guild.id)

    async def close(self):
        """Graceful shutdown procedure."""
        log.info("action=bot_shutdown msg=Starting graceful shutdown")
        
        # Cancel scheduler
        try:
            self.scheduler_service.stop()
        except Exception as e:
            log.error(f"action=shutdown_error component=scheduler error={e}")

        # Close HTTP sessions
        try:
            await self.rss_service.close()
        except Exception as e:
            log.error(f"action=shutdown_error component=rss_service error={e}")
            
        await super().close()
        log.info("action=bot_shutdown msg=Shutdown complete")

    async def on_command_error(self, context: commands.Context, exception: commands.CommandError) -> None:
        """Global error handler for commands."""
        if isinstance(exception, commands.CommandNotFound):
            return
            
        log.warning(f"action=command_error command={context.command} error={exception}")
        
        if not getattr(context.command, "has_error_handler", lambda: False)():
            # Only send basic error if there's no specific handler
            if isinstance(exception, commands.MissingRequiredArgument):
                await context.send(view=ComponentService.create_error_message("Usage Error", str(exception)))
            elif isinstance(exception, commands.CheckFailure):
                pass # Usually handled by decorators
            else:
                await context.send(view=ComponentService.create_error_message("Error", "An unexpected error occurred."))
