import discord
import os
import psutil
from discord import ui
from discord.ext import commands
from utils.permissions import is_owner
from services.release_service import ReleaseService
from services.database_service import DatabaseService
from services.rss_service import RSSService
from services.component_service import ComponentService
from services.translation_service import TranslationService

class AdminCog(commands.Cog):
    def __init__(self, bot: commands.Bot, release_service: ReleaseService, db_service: DatabaseService, rss_service: RSSService, translation_service: TranslationService):
        self.bot = bot
        self.release_service = release_service
        self.db_service = db_service
        self.rss_service = rss_service
        self.translation_service = translation_service

    @commands.command(name="test")
    @is_owner()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def test_cmd(self, ctx: commands.Context):
        """Run an end-to-end test (Owner only)."""
        msg = await ctx.send("Starting test... Fetching RSS feed.", delete_after=5)
        try:
            releases = await self.rss_service.fetch_feed()
            if not releases:
                await ctx.send(view=ComponentService.create_info_message("Test", "No releases found in RSS feed."))
                return

            newest = releases[0]
            
            # Translate to English
            translated_newest = await self.translation_service.translate_release(newest)
            
            view = ComponentService.create_release_message(translated_newest)
            
            # Components V2 cannot have top-level message content
            await ctx.send(view=ComponentService.create_success_message("Test Successful", "Here is a preview of the newest release:"))
            await ctx.send(view=view)
        except Exception as e:
            await ctx.send(view=ComponentService.create_error_message("Test Failed", str(e)))

    @commands.command(name="fetch")
    @is_owner()
    @commands.cooldown(1, 30, commands.BucketType.user)
    async def fetch_cmd(self, ctx: commands.Context):
        """Immediately perform an RSS check (Owner only)."""
        msg = await ctx.send("Triggering immediate RSS fetch...")
        try:
            await self.release_service.check_and_post_new_releases()
            await msg.edit(content="RSS fetch completed successfully.")
            await msg.delete(delay=5)
        except Exception as e:
            await msg.edit(content=f"RSS fetch failed: {e}")
            await msg.delete(delay=5)

    @commands.command(name="health")
    @is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def health_cmd(self, ctx: commands.Context):
        """Display bot health and statistics (Owner only)."""
        process = psutil.Process(os.getpid())
        mem_info = process.memory_info()
        mem_mb = mem_info.rss / 1024 / 1024
        
        guilds = len(self.bot.guilds)
        configured_channels = len([g for g in self.db_service.get_all_guilds().values() if g.get("channel_id")])
        
        state = self.db_service.get_state()
        last_fetch = state.get("last_fetch", "Never")
        
        scheduler = self.bot.scheduler_service  # injected dynamically in bot setup
        scheduler_status = f"Running (Interval: {scheduler.daily_fetch.minutes}m)" if scheduler.daily_fetch.is_running() else "Stopped"
        
        view = ui.LayoutView(timeout=None)
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        content = (
            "### Bot Health Status\n"
            f"**Memory Usage:** {mem_mb:.2f} MB\n"
            f"**Guilds:** {guilds}\n"
            f"**Configured Channels:** {configured_channels}\n"
            f"**Scheduler Status:** {scheduler_status}\n"
            f"**Last Fetch:** {last_fetch}"
        )
        main_section = ui.Section(ui.TextDisplay(content), accessory=ui.Thumbnail(media=thumb_url))
        container = ui.Container(main_section)
        view.add_item(container)
        await ctx.send(view=view)

    @commands.command(name="reload")
    @is_owner()
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def reload_cmd(self, ctx: commands.Context):
        """Reload configuration and database (Owner only)."""
        try:
            # Re-read database
            self.db_service.__init__()
            await ctx.send(view=ComponentService.create_success_message("Reload", "Database and configuration reloaded successfully."))
        except Exception as e:
            await ctx.send(view=ComponentService.create_error_message("Reload Failed", str(e)))

    @commands.command(name="ping")
    @is_owner()
    @commands.cooldown(1, 5, commands.BucketType.user)
    async def ping_cmd(self, ctx: commands.Context):
        """Check the bot's latency (Owner only)."""
        import time
        ws_latency = round(self.bot.latency * 1000)
        
        # We create a placeholder view to calculate accurate roundtrip API latency
        view = ui.LayoutView(timeout=None)
        content = f"### Latency Test\n**WebSocket:** {ws_latency}ms\n**API Response:** Calculating..."
        main_section = ui.Section(ui.TextDisplay(content))
        view.add_item(ui.Container(main_section))
        
        start_time = time.monotonic()
        msg = await ctx.send(view=view)
        end_time = time.monotonic()
        
        api_latency = round((end_time - start_time) * 1000)
        
        # Update view with accurate results
        updated_view = ui.LayoutView(timeout=None)
        updated_content = f"### Latency\n**WebSocket:** {ws_latency}ms\n**API Response:** {api_latency}ms"
        updated_section = ui.Section(ui.TextDisplay(updated_content))
        updated_view.add_item(ui.Container(updated_section))
        
        await msg.edit(view=updated_view)

    @test_cmd.error
    @fetch_cmd.error
    @health_cmd.error
    @ping_cmd.error
    @reload_cmd.error
    async def owner_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CheckFailure):
            await ctx.send(view=ComponentService.create_error_message("Permission Denied", "This command is restricted to the bot owner."))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(view=ComponentService.create_error_message("Cooldown", f"Please wait {error.retry_after:.2f}s."))
        else:
            await ctx.send(view=ComponentService.create_error_message("Error", str(error)))

async def setup(bot):
    await bot.add_cog(AdminCog(bot, bot.release_service, bot.db_service, bot.rss_service, bot.translation_service))
