import discord
from discord.ext import commands
from services.rss_service import RSSService
from services.component_service import ComponentService
from services.translation_service import TranslationService
from utils.logger import log

class UpdatesCog(commands.Cog):
    def __init__(self, bot: commands.Bot, rss_service: RSSService, translation_service: TranslationService):
        self.bot = bot
        self.rss_service = rss_service
        self.translation_service = translation_service

    @commands.command(name="updates")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def updates_cmd(self, ctx: commands.Context):
        """View the latest game updates on Online-Fix."""
        msg = await ctx.send(view=ComponentService.create_info_message("Fetching Updates", "Pulling the latest drops..."))
        
        try:
            results = await self.rss_service.get_recent_updates(limit=50)
            
            if not results:
                await msg.edit(view=ComponentService.create_error_message("Error", "Could not retrieve recent updates."))
                return
                
            view = ComponentService.create_paginated_view("Latest Updates", results, self.translation_service)
            await msg.delete()
            await view.start(ctx)
            
        except Exception as e:
            log.error(f"action=updates_command_failed error={e}")
            await msg.edit(view=ComponentService.create_error_message("Error Failed", str(e)))

    @commands.command(name="trending")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def trending_cmd(self, ctx: commands.Context):
        """View the most popular/trending games."""
        msg = await ctx.send(view=ComponentService.create_info_message("Trending", "Finding out what's hot right now..."))
        
        try:
            results = await self.rss_service.get_trending(limit=30)
            if not results:
                await msg.edit(view=ComponentService.create_error_message("Error", "Could not retrieve trending games."))
                return
                
            view = ComponentService.create_paginated_view("Trending Games", results, self.translation_service)
            await msg.delete()
            await view.start(ctx)
        except Exception as e:
            log.error(f"action=trending_command_failed error={e}")
            await msg.edit(view=ComponentService.create_error_message("Error", str(e)))

    @commands.command(name="genre")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def genre_cmd(self, ctx: commands.Context, *, genre: str = None):
        """Browse games by a specific genre (e.g. shooter, rpg)."""
        if not genre:
            genres_list = "shooter, rpg, action, horror, survival, strategy, simulator, co-op"
            await ctx.send(view=ComponentService.create_info_message("Genres", f"Please provide a genre!\n\n**Common Genres:**\n`{genres_list}`\n\n**Example:** `!genre shooter`"))
            return
            
        msg = await ctx.send(view=ComponentService.create_info_message("Fetching", f"Looking up `{genre}` games..."))
        
        try:
            results = await self.rss_service.get_genre(genre, limit=50)
            if not results:
                await msg.edit(view=ComponentService.create_error_message("Not Found", f"No games found for genre `{genre}`."))
                return
                
            view = ComponentService.create_paginated_view(f"Genre: {genre.capitalize()}", results, self.translation_service, genre)
            await msg.delete()
            await view.start(ctx)
        except Exception as e:
            log.error(f"action=genre_command_failed error={e}")
            await msg.edit(view=ComponentService.create_error_message("Error", str(e)))

    @updates_cmd.error
    @trending_cmd.error
    @genre_cmd.error
    async def cog_command_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.CommandOnCooldown):
            await ctx.send(view=ComponentService.create_error_message("Cooldown", f"Please wait {error.retry_after:.1f}s."))
        elif isinstance(error, commands.MissingRequiredArgument):
            pass # Handled internally where needed
        else:
            await ctx.send(view=ComponentService.create_error_message("Error", str(error)))

async def setup(bot):
    await bot.add_cog(UpdatesCog(bot, bot.rss_service, bot.translation_service))
