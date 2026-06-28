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
            results = await self.rss_service.search_games(query, limit=10)
            
            view = discord.ui.LayoutView(timeout=None)
            thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
            
            if not results:
                content = f"### Search Results: `{query}`\n\nThat game isn't in our database yet!"
                main_section = discord.ui.Section(
                    discord.ui.TextDisplay(content),
                    accessory=discord.ui.Thumbnail(media=thumb_url)
                )
                view.add_item(discord.ui.Container(main_section))
                await msg.delete()
                await ctx.send(view=view)
                return
                
            import asyncio
            translated_titles = await asyncio.gather(
                *(self.translation_service.translate_text(res.title) for res in results),
                return_exceptions=True
            )
            
            content = f"### Search Results: `{query}`\n\n"
            for idx, res in enumerate(results):
                title = translated_titles[idx] if not isinstance(translated_titles[idx], Exception) else res.title
                content += f"**{idx+1}.** [{title}]({res.link})\n"
                
            main_section = discord.ui.Section(
                discord.ui.TextDisplay(content),
                accessory=discord.ui.Thumbnail(media=thumb_url)
            )
            view.add_item(discord.ui.Container(main_section))
            
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
