from datetime import datetime, timezone
import asyncio
from typing import List
from utils.logger import log
from services.rss_service import RSSService
from services.database_service import DatabaseService
from services.channel_service import ChannelService
from services.component_service import ComponentService
from services.translation_service import TranslationService

class ReleaseService:
    def __init__(self, rss_service: RSSService, db_service: DatabaseService, channel_service: ChannelService, component_service: ComponentService, translation_service: TranslationService):
        self.rss_service = rss_service
        self.db_service = db_service
        self.channel_service = channel_service
        self.component_service = component_service
        self.translation_service = translation_service

    async def check_and_post_new_releases(self) -> None:
        """Fetches the RSS feed and posts newly discovered games."""
        log.info("action=check_releases status=started")
        
        try:
            releases = await self.rss_service.fetch_feed()
            if not releases:
                log.info("action=check_releases status=no_new_items")
                return

            new_releases = []
            for release in releases:
                if not self.db_service.is_game_posted(release.guid):
                    new_releases.append(release)

            # Reverse to post oldest first (if feed is newest first)
            new_releases.reverse()

            for release in new_releases:
                # Translate Russian strings to English automatically
                translated_release = await self.translation_service.translate_release(release)
                
                view = self.component_service.create_release_message(translated_release)
                
                await self.channel_service.broadcast_release(view)
                
                # Mark as posted only after successful broadcast iteration
                timestamp = datetime.now(timezone.utc).isoformat()
                self.db_service.mark_game_posted(release.guid, release.title, timestamp)
                log.info(f"action=game_posted guid={release.guid} title={release.title}")
                
                # Rate limiting between different games
                await asyncio.sleep(2)

            self.db_service.update_state("last_fetch", datetime.now(timezone.utc).isoformat())
            log.info(f"action=check_releases status=completed new_count={len(new_releases)}")

        except Exception as e:
            log.error(f"action=check_releases_failed error={e}")
            await self.channel_service.notify_owner("Critical Failure: RSS Fetch", str(e))

