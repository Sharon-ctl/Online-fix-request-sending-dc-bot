import discord
from discord import ui
from discord.ext import commands
from services.component_service import ComponentService

class CustomHelpCommand(commands.HelpCommand):
    def __init__(self):
        super().__init__(command_attrs={
            "help": "Display information about the bot and all available commands.",
            "cooldown": commands.CooldownMapping.from_cooldown(1, 5, commands.BucketType.user)
        })

    async def send_bot_help(self, mapping):
        view = ui.LayoutView(timeout=None)
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        
        content = "**Games!! Tracker Help**\n*A simple bot to monitor new game releases, track trending games, and browse genres.*\n\n"
        
        for cog, cmds in mapping.items():
            filtered = await self.filter_commands(cmds, sort=True)
            if filtered:
                cog_name = getattr(cog, "qualified_name", "No Category")
                if cog_name == "AdminCog":
                    continue
                cmds_desc = "\n".join([f"`!{c.name}` - {c.short_doc}" for c in filtered])
                content += f"**{cog_name}**\n{cmds_desc}\n\n"
                
        content += "*Type `!help <command>` for more details.*"
        
        main_section = ui.Section(ui.TextDisplay(content), accessory=ui.Thumbnail(media=thumb_url))
        container = ui.Container(main_section)
        view.add_item(container)
        await self.get_destination().send(view=view)

    async def send_command_help(self, command):
        view = ui.LayoutView(timeout=None)
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        
        desc = command.help or "No description provided."
        content = f"**Command:** `!{command.name}`\n{desc}\n\n"
        
        if command.aliases:
            aliases_str = ", ".join(command.aliases)
            content += f"**Aliases:** {aliases_str}\n"
            
        content += f"**Usage:** `!{command.name} {command.signature}`"
        
        main_section = ui.Section(ui.TextDisplay(content), accessory=ui.Thumbnail(media=thumb_url))
        container = ui.Container(main_section)
        view.add_item(container)
        await self.get_destination().send(view=view)

class HelpCog(commands.Cog):
    def __init__(self, bot: commands.Bot):
        self.bot = bot
        self._original_help_command = bot.help_command
        bot.help_command = CustomHelpCommand()
        bot.help_command.cog = self

    def cog_unload(self):
        self.bot.help_command = self._original_help_command

async def setup(bot):
    await bot.add_cog(HelpCog(bot))
