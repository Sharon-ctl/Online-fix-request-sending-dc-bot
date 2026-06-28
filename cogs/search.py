import discord
from discord.ext import commands
from services.rss_service import RSSService
from services.component_service import ComponentService
from services.translation_service import TranslationService
from utils.logger import log

class SearchCog(commands.Cog):
    def __init__(self, bot: commands.Bot, rss_service: RSSService, translation_service: TranslationService):
        self.bot = bot
        self.rss_service = rss_service
        self.translation_service = translation_service

    @commands.command(name="search")
    @commands.cooldown(1, 10, commands.BucketType.user)
    async def search_cmd(self, ctx: commands.Context, *, query: str):
        """Search for a game in the Online-Fix database."""
        msg = await ctx.send(view=ComponentService.create_info_message("Searching", f"Looking up `{query}`..."))
        
        try:
            result = await self.rss_service.search_game(query)
            if not result:
                await msg.edit(view=ComponentService.create_error_message("Not Found", f"No games found for `{query}`."))
                return
                
            translated = await self.translation_service.translate_release(result)
            view = ComponentService.create_release_message(translated)
            
            await msg.delete()
            await ctx.send(view=view)
            
        except Exception as e:
            log.error(f"action=search_command_failed error={e}")
            await msg.edit(view=ComponentService.create_error_message("Search Failed", str(e)))

    @search_cmd.error
    async def search_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(view=ComponentService.create_error_message("Usage Error", "Please provide a search query. Example: `!search minecraft`"))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(view=ComponentService.create_error_message("Cooldown", f"Please wait {error.retry_after:.1f}s."))
        else:
            await ctx.send(view=ComponentService.create_error_message("Error", str(error)))

async def setup(bot):
    await bot.add_cog(SearchCog(bot, bot.rss_service, bot.translation_service))
