import asyncio
import feedparser
import cloudscraper
from typing import List, Optional
from utils.constants import RSS_URL, HTTP_TIMEOUT, HTTP_RETRIES
from utils.logger import log
from utils.exceptions import RSSFetchError, RSSParseError
from utils.parser import parse_rss_entry, ReleaseData
from services.database_service import DatabaseService

class RSSService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        # Use cloudscraper to bypass Cloudflare anti-bot checks (JS challenges and TLS fingerprints)
        self.scraper = cloudscraper.create_scraper(
            browser={
                'browser': 'chrome',
                'platform': 'windows',
                'desktop': True
            }
        )

    async def initialize(self):
        pass  # cloudscraper handles connections internally

    async def close(self):
        if self.scraper:
            self.scraper.close()

    def _sync_fetch(self, headers: dict):
        # Synchronous fetch method to be run in a thread
        response = self.scraper.get(RSS_URL, headers=headers, timeout=HTTP_TIMEOUT)
        return response.status_code, response.headers, response.text

    async def fetch_feed(self) -> List[ReleaseData]:
        state = self.db_service.get_state()
        headers = {
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
                
                # Execute blocking cloudscraper in background thread
                status, resp_headers, content = await asyncio.to_thread(self._sync_fetch, headers)
                
                if status == 304:
                    log.info("action=rss_fetch status=304_not_modified")
                    return []
                    
                if status == 429 or status == 403:
                    log.warning(f"action=rss_fetch status={status}_blocked")
                    if delay:
                        await asyncio.sleep(delay)
                        continue
                    raise RSSFetchError(f"Rate limited or forbidden (Status {status}).")

                if status >= 400:
                    raise RSSFetchError(f"HTTP Error {status}")
                    
                # Update cache headers
                if "ETag" in resp_headers:
                    self.db_service.update_state("rss_etag", resp_headers["ETag"])
                if "Last-Modified" in resp_headers:
                    self.db_service.update_state("rss_modified", resp_headers["Last-Modified"])

                return self._parse_feed_content(content)

            except Exception as e:
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
