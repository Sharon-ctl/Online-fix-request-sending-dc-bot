import discord
from discord import ui
from typing import Optional
from utils.parser import ReleaseData
from utils.constants import EMBED_COLOR

class ReleaseLayout(ui.LayoutView):
    def __init__(self, release: ReleaseData):
        super().__init__(timeout=None)
        
        # Valid PNG logo for the accessory thumbnail
        logo_url = "https://online-fix.me/templates/Default/images/logo.png"
        
        # Combine everything into a single markdown string
        content = f"### [{release.title}]({release.link})\n"
            
        details = []
        if release.release_date:
            details.append(f"**Release Date:** {release.release_date}")
        if release.play_via:
            details.append(f"**Play Via:** {release.play_via}")
        if release.modes:
            details.append(f"**Modes:** {release.modes}")
        if release.categories:
            details.append(f"**Categories:** {release.categories}")
            
        if details:
            content += "\n".join(details) + "\n\n"
            
        content += f"*Published: {release.published}*"
        
        # Determine the thumbnail for the section
        # Cloudflare blocks the actual game posters for Discord, so we use the website logo as requested.
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        
        # Create a single Section containing all the text and images
        main_section = ui.Section(
            ui.TextDisplay(content),
            accessory=ui.Thumbnail(media=thumb_url)
        )
        
        container = ui.Container(main_section)
        
        # Add Link Button wrapped in an ActionRow
        action_row = ui.ActionRow(ui.Button(label="Open Release Page", url=release.link, style=discord.ButtonStyle.link))
        container.add_item(action_row)
        
        self.add_item(container)

class ComponentService:
    @staticmethod
    def create_release_message(release: ReleaseData) -> ui.LayoutView:
        """Creates the Components V2 LayoutView for a release message."""
        return ReleaseLayout(release)

    @staticmethod
    def create_message(title: str, description: str) -> ui.LayoutView:
        view = ui.LayoutView(timeout=None)
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        
        main_section = ui.Section(
            ui.TextDisplay(f"### {title}\n{description}"),
            accessory=ui.Thumbnail(media=thumb_url)
        )
        
        container = ui.Container(main_section)
        view.add_item(container)
        return view

    @staticmethod
    def create_success_message(title: str, description: str) -> ui.LayoutView:
        return ComponentService.create_message(title, description)

    @staticmethod
    def create_error_message(title: str, description: str) -> ui.LayoutView:
        return ComponentService.create_message(title, description)

    @staticmethod
    def create_info_message(title: str, description: str) -> ui.LayoutView:
        return ComponentService.create_message(title, description)
