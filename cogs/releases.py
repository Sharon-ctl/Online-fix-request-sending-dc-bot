import discord
from discord.ext import commands
from utils.permissions import has_manage_server, validate_bot_channel_permissions
from services.database_service import DatabaseService
from services.component_service import ComponentService

class ReleasesCog(commands.GroupCog, group_name="channel"):
    def __init__(self, bot: commands.Bot, db_service: DatabaseService):
        self.bot = bot
        self.db_service = db_service

    @commands.command(name="set")
    @has_manage_server()
    @commands.cooldown(1, 10, commands.BucketType.guild)
    async def set_channel(self, ctx: commands.Context, channel: discord.TextChannel):
        """Configure the channel for RSS releases."""
        
        if not ctx.guild or not ctx.guild.me:
            await ctx.send(view=ComponentService.create_error_message("Error", "Guild information unavailable."))
            return

        can_send, missing = validate_bot_channel_permissions(channel, ctx.guild.me)
        
        if not can_send:
            missing_str = ", ".join(missing)
            await ctx.send(view=ComponentService.create_error_message(
                "Missing Permissions", 
                f"I cannot be configured for {channel.mention} because I am missing the following permissions:\n\n{missing_str}"
            ))
            return

        try:
            self.db_service.set_guild_channel(ctx.guild.id, channel.id)
            await ctx.send(view=ComponentService.create_success_message(
                "Channel Configured", 
                f"Successfully set {channel.mention} as the release channel."
            ))
        except Exception as e:
            await ctx.send(view=ComponentService.create_error_message("Database Error", f"Failed to save configuration: {e}"))

    @set_channel.error
    async def set_channel_error(self, ctx: commands.Context, error):
        if isinstance(error, commands.MissingRequiredArgument):
            await ctx.send(view=ComponentService.create_error_message("Usage Error", "Please specify a channel. Example: `!channel set #releases`"))
        elif isinstance(error, commands.ChannelNotFound):
            await ctx.send(view=ComponentService.create_error_message("Error", "Channel not found. Please mention a valid text channel."))
        elif isinstance(error, commands.CheckFailure):
            await ctx.send(view=ComponentService.create_error_message("Permission Denied", "You need `Manage Server` permissions to use this command."))
        elif isinstance(error, commands.CommandOnCooldown):
            await ctx.send(view=ComponentService.create_error_message("Cooldown", f"Please wait {error.retry_after:.2f}s."))
        else:
            await ctx.send(view=ComponentService.create_error_message("Error", str(error)))

async def setup(bot):
    await bot.add_cog(ReleasesCog(bot, bot.db_service))
