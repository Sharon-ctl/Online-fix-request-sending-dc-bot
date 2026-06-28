import discord
from discord import ui
import asyncio

class MockRelease:
    title = "Test Game"
    link = "https://example.com"
    image_url = "https://example.com/image.png"
    release_date = "Today"
    play_via = "Steam"
    modes = "Co-op"
    categories = "Action"
    published = "Now"

class ReleaseLayout(ui.LayoutView):
    def __init__(self, release):
        super().__init__(timeout=None)
        logo_url = "https://online-fix.me/templates/Default/images/logo.png"
        content = f"### [{release.title}]({release.link})\n"
        if release.image_url:
            content += f"![Game Image]({release.image_url})\n\n"
        
        content += f"**Release Date:** {release.release_date}\n**Play Via:** {release.play_via}\n**Modes:** {release.modes}\n**Categories:** {release.categories}\n\n*Published: {release.published}*"
        
        main_section = ui.Section(ui.TextDisplay(content), accessory=ui.Thumbnail(media=logo_url))
        container = ui.Container(main_section)
        action_row = ui.ActionRow(ui.Button(label="Open Release Page", url=release.link, style=discord.ButtonStyle.link))
        container.add_item(action_row)
        self.add_item(container)

layout = ReleaseLayout(MockRelease())
print(layout.to_components())
