import asyncio
import aiohttp
import feedparser
from typing import List, Optional
from utils.constants import RSS_URL, HTTP_TIMEOUT, HTTP_RETRIES
from utils.logger import log
from utils.exceptions import RSSFetchError, RSSParseError
from utils.parser import parse_rss_entry, ReleaseData
from services.database_service import DatabaseService

class RSSService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.session: Optional[aiohttp.ClientSession] = None

    async def initialize(self):
        if self.session is None or self.session.closed:
            self.session = aiohttp.ClientSession(
                timeout=aiohttp.ClientTimeout(total=HTTP_TIMEOUT)
            )

    async def close(self):
        if self.session and not self.session.closed:
            await self.session.close()

    async def fetch_feed(self) -> List[ReleaseData]:
        await self.initialize()
        
        state = self.db_service.get_state()
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept": "application/rss+xml, application/xml, text/xml, */*",
            "Accept-Language": "en-US,en;q=0.9"
        }
        if state.get("rss_etag"):
            headers["If-None-Match"] = state["rss_etag"]
        if state.get("rss_modified"):
            headers["If-Modified-Since"] = state["rss_modified"]

        for attempt, delay in enumerate(HTTP_RETRIES + [0]):
            try:
                log.debug(f"Fetching RSS feed (Attempt {attempt + 1})")
                async with self.session.get(RSS_URL, headers=headers) as response:
                    if response.status == 304:
                        log.info("action=rss_fetch status=304_not_modified")
                        return []
                        
                    if response.status == 429:
                        log.warning("action=rss_fetch status=429_ratelimit")
                        if delay:
                            await asyncio.sleep(delay)
                            continue
                        raise RSSFetchError("Rate limited consistently.")

                    response.raise_for_status()
                    
                    # Update cache headers
                    if "ETag" in response.headers:
                        self.db_service.update_state("rss_etag", response.headers["ETag"])
                    if "Last-Modified" in response.headers:
                        self.db_service.update_state("rss_modified", response.headers["Last-Modified"])

                    content = await response.text()
                    return self._parse_feed_content(content)

            except aiohttp.ClientError as e:
                log.warning(f"action=rss_fetch_failed error={e} attempt={attempt + 1}")
                if delay:
                    await asyncio.sleep(delay)
                else:
                    raise RSSFetchError(f"Failed to fetch RSS feed after {len(HTTP_RETRIES)+1} attempts: {e}")
                    
        return []

    def _parse_feed_content(self, content: str) -> List[ReleaseData]:
        try:
            feed = feedparser.parse(content)
            if feed.bozo and hasattr(feed, 'bozo_exception'):
                # feedparser sets bozo to 1 on malformed XML
                log.warning(f"action=rss_parse_warning exception={feed.bozo_exception}")
                
            entries = []
            for entry in feed.entries:
                try:
                    release = parse_rss_entry(entry)
                    entries.append(release)
                except RSSParseError as e:
                    log.warning(f"action=rss_entry_skip error={e}")
                    
            return entries
            
        except Exception as e:
            raise RSSParseError(f"Failed to parse the feed wrapper: {e}")
