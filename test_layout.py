import discord.ui as ui
import discord
from utils.parser import ReleaseData
from services.component_service import ReleaseLayout

release = ReleaseData(
    guid="123",
    title="Test Game",
    link="http://example.com",
    published="Today",
    image_url="http://example.com/image.png",
    release_date="Now"
)

layout = ReleaseLayout(release)
print(layout.to_components())
