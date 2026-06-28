from typing import Tuple, List
import discord
from discord.ext import commands

def is_owner():
    """A command decorator that checks if the user is the bot owner."""
    async def predicate(ctx: commands.Context) -> bool:
        if not await ctx.bot.is_owner(ctx.author):
            return False
        return True
    return commands.check(predicate)

def has_manage_server():
    """A command decorator that checks if the user has Manage Server permission."""
    async def predicate(ctx: commands.Context) -> bool:
        if not ctx.guild:
            return False
        if getattr(ctx.author.guild_permissions, "manage_guild", False):
            return True
        return await ctx.bot.is_owner(ctx.author)
    return commands.check(predicate)

def validate_bot_channel_permissions(channel: discord.TextChannel, bot_member: discord.Member) -> Tuple[bool, List[str]]:
    """
    Validates if the bot has required permissions in the given channel.
    Returns (True, []) if all good, (False, [missing_perms]) if not.
    """
    required_permissions = {
        "view_channel": "View Channel",
        "send_messages": "Send Messages",
        "embed_links": "Embed Links",
        "attach_files": "Attach Files"
    }

    perms = channel.permissions_for(bot_member)
    missing = []

    for perm_attr, perm_name in required_permissions.items():
        if not getattr(perms, perm_attr, False):
            missing.append(perm_name)

    return len(missing) == 0, missing
