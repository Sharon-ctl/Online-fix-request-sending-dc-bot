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

class PaginatedReleaseView(ui.LayoutView):
    def __init__(self, title: str, results: list[ReleaseData], translation_service, query: str = ""):
        super().__init__(timeout=600) # 10 minute timeout to clear memory
        self.view_title = title
        self.results = results
        self.translation_service = translation_service
        self.query = query
        self.current_page = 0
        self.per_page = 10
        self.max_pages = max(1, (len(results) - 1) // self.per_page + 1)
        self.message = None
        
    async def on_timeout(self):
        """Memory leak prevention: Clean up large result arrays when the view expires."""
        self.results.clear()
        
        # Disable all buttons
        for child in self.children:
            if hasattr(child, 'children'):
                for item in child.children:
                    item.disabled = True
                    
        if self.message:
            try:
                await self.message.edit(view=self)
            except Exception:
                pass

    def _clean_title(self, title: str) -> str:
        """Instantly localizes the title without making expensive/slow API calls to Google Translate."""
        import re
        cleaned = re.sub(r'(?i)по сети.*', '', title)
        cleaned = re.sub(r'(?i)по интернету.*', '', cleaned)
        return cleaned.strip()

    async def build_page(self) -> ui.Container:
        start_idx = self.current_page * self.per_page
        end_idx = start_idx + self.per_page
        page_results = self.results[start_idx:end_idx]
        
        header = f"### {self.view_title}"
        if self.query:
            header += f": `{self.query}`"
            
        if self.max_pages > 1:
            header += f" (Page {self.current_page + 1}/{self.max_pages})"
        header += "\n\n"
        
        content = header
        if not page_results:
            content += "No results found."
        else:
            for idx, res in enumerate(page_results):
                # Use instant regex cleaning instead of slow blocking API translation
                clean_name = self._clean_title(res.title)
                content += f"**{start_idx + idx + 1}.** [{clean_name}]({res.link})\n"
                
        thumb_url = "https://cdn.discordapp.com/attachments/1402112765140799609/1520700767164698634/oflogo.gif?ex=6a422674&is=6a40d4f4&hm=612797893b90e25e5504ed65c0950eb8f8ac377d5d91c273af9cdadc8e64c484&"
        
        main_section = ui.Section(
            ui.TextDisplay(content),
            accessory=ui.Thumbnail(media=thumb_url)
        )
        
        container = ui.Container(main_section)
        
        if self.max_pages > 1:
            buttons = []
            
            prev_btn = ui.Button(label="<", style=discord.ButtonStyle.secondary, disabled=self.current_page == 0)
            async def prev_callback(interaction: discord.Interaction):
                self.current_page -= 1
                await self.update_message(interaction)
            prev_btn.callback = prev_callback
            buttons.append(prev_btn)
            
            next_btn = ui.Button(label=">", style=discord.ButtonStyle.secondary, disabled=self.current_page == self.max_pages - 1)
            async def next_callback(interaction: discord.Interaction):
                self.current_page += 1
                await self.update_message(interaction)
            next_btn.callback = next_callback
            buttons.append(next_btn)
            
            action_row = ui.ActionRow(*buttons)
            container.add_item(action_row)
            
        return container

    async def update_message(self, interaction: discord.Interaction):
        self.clear_items()
        container = await self.build_page()
        self.add_item(container)
        await interaction.response.edit_message(view=self)

    async def start(self, messageable):
        self.clear_items()
        container = await self.build_page()
        self.add_item(container)
        self.message = await messageable.send(view=self)
        return self.message

class ComponentService:
    @staticmethod
    def create_paginated_view(title: str, results: list[ReleaseData], translation_service, query: str = "") -> PaginatedReleaseView:
        return PaginatedReleaseView(title, results, translation_service, query)

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
