import asyncio
import feedparser
from curl_cffi import requests
from typing import List, Optional
from utils.constants import RSS_URL, HTTP_TIMEOUT, HTTP_RETRIES
from utils.logger import log
from utils.exceptions import RSSFetchError, RSSParseError
from utils.parser import parse_rss_entry, parse_fitgirl_rss_entry, ReleaseData
from services.database_service import DatabaseService

class RSSService:
    def __init__(self, db_service: DatabaseService):
        self.db_service = db_service
        self.session = None

    async def initialize(self):
        # Create a single persistent session to pool connections, improving speed and stopping memory leaks
        self.session = requests.Session(impersonate="chrome110")
        self.session.timeout = HTTP_TIMEOUT

    async def close(self):
        if self.session:
            self.session.close()

    def _sync_fetch(self, url: str, headers: dict):
        try:
            response = self.session.get(url, headers=headers)
            return response.status_code, response.headers, response.text
        except Exception as e:
            raise RSSFetchError(f"HTTP Fetch failed for {url}: {str(e)}")

    def _sync_search_of(self, query: str):
        try:
            url = "https://online-fix.me/index.php?do=search"
            data = {
                "do": "search",
                "subaction": "search",
                "story": query
            }
            response = self.session.post(url, data=data)
            return response.status_code, response.text
        except Exception as e:
            raise RSSFetchError(f"OF Search POST failed: {str(e)}")

    def _sync_fetch_url(self, url: str):
        try:
            response = self.session.get(url)
            return response.status_code, response.text
        except Exception as e:
            raise RSSFetchError(f"URL GET failed: {str(e)}")

    def _interleave_results(self, list1: List[ReleaseData], list2: List[ReleaseData], limit: int) -> List[ReleaseData]:
        result = []
        # Alternating weave to give a fair mix of both sources
        for a, b in zip(list1, list2):
            result.extend([a, b])
        
        # Add remaining if one list is longer
        if len(list1) > len(list2):
            result.extend(list1[len(list2):])
        elif len(list2) > len(list1):
            result.extend(list2[len(list1):])
            
        return result[:limit]

    async def get_recent_updates(self, limit: int = 50) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        results = []
        try:
            status, content = await asyncio.to_thread(self._sync_fetch_url, "https://online-fix.me/")
            if status < 400:
                soup = BeautifulSoup(content, 'html.parser')
                articles = soup.find_all('div', class_='article') or soup.find_all('article', class_='article')
                for article in articles[:limit]:
                    res = parse_html_article(article)
                    if res: results.append(res)
        except Exception as e:
            log.error(f"action=get_recent_updates_of_failed error={e}")

        return results

    async def get_genre(self, genre: str, limit: int = 50) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        results = []
        genre_clean = genre.lower().strip()
        
        try:
            status, content = await asyncio.to_thread(self._sync_fetch_url, f"https://online-fix.me/games/{genre_clean}/")
            if status < 400:
                soup = BeautifulSoup(content, 'html.parser')
                articles = soup.find_all('div', class_='article') or soup.find_all('article', class_='article')
                for article in articles[:limit]:
                    res = parse_html_article(article)
                    if res: results.append(res)
        except Exception:
            pass
            
        if not results:
            return await self.search_games(genre, limit)
        return results

    async def get_trending(self, limit: int = 50) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        
        trending = []
        try:
            status, content = await asyncio.to_thread(self._sync_fetch_url, "https://online-fix.me/")
            if status < 400:
                soup = BeautifulSoup(content, 'html.parser')
                blocks = soup.find_all('div', class_='top-news') or soup.find_all('ul', class_='top-news')
                for block in blocks:
                    for a in block.find_all('a'):
                        if 'href' in a.attrs and len(a.text.strip()) > 3:
                            trending.append(ReleaseData(
                                guid=a['href'], title=a.text.strip(), link=a['href'],
                                published="", source="Online-Fix"
                            ))
        except Exception:
            pass
            
        if not trending:
            return await self.get_recent_updates(limit)
            
        return trending[:limit]

    async def search_games(self, query: str, limit: int = 50) -> List[ReleaseData]:
        # KEEP FITGIRL IN SEARCH AS REQUESTED
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article, parse_fitgirl_article
        
        of_results = []
        fg_results = []
        
        async def fetch_of():
            try:
                status, content = await asyncio.to_thread(self._sync_search_of, query)
                if status < 400:
                    soup = BeautifulSoup(content, 'html.parser')
                    articles = soup.find_all('div', class_='article') or soup.find_all('article', class_='article')
                    for article in articles[:limit]:
                        res = parse_html_article(article)
                        if res: of_results.append(res)
            except Exception as e:
                log.warning(f"OF search failed: {e}")
                
        async def fetch_fg():
            try:
                # FitGirl WordPress Search is very slow. We enforce a strict timeout here so it doesn't drag down the bot.
                search_url = f"https://fitgirl-repacks.site/?s={query.replace(' ', '+')}"
                status, content = await asyncio.to_thread(self._sync_fetch_url, search_url)
                if status < 400:
                    soup = BeautifulSoup(content, 'html.parser')
                    articles = soup.find_all('article')
                    for article in articles[:limit]:
                        res = parse_fitgirl_article(article)
                        if res: fg_results.append(res)
            except Exception as e:
                log.warning(f"FG search failed or timed out: {e}")

        # Gather OF normally, but force FG to timeout after 2.5 seconds to keep the bot snappy
        await asyncio.gather(
            fetch_of(),
            asyncio.wait_for(fetch_fg(), timeout=2.5)
        )
        return self._interleave_results(of_results, fg_results, limit)

    async def fetch_feed(self) -> List[ReleaseData]:
        # REMOVED FITGIRL FROM AUTO-POSTER FEED AS REQUESTED
        state = self.db_service.get_state()
        headers = {"Accept": "application/rss+xml, application/xml, text/xml, */*", "Accept-Language": "en-US,en;q=0.9"}
        
        if state.get("rss_etag"): headers["If-None-Match"] = state["rss_etag"]
        if state.get("rss_modified"): headers["If-Modified-Since"] = state["rss_modified"]
        
        entries = []
        for attempt, delay in enumerate(HTTP_RETRIES + [0]):
            try:
                status, resp_headers, content = await asyncio.to_thread(self._sync_fetch, RSS_URL, headers)
                if status == 304: return []
                if status == 429 or status == 403:
                    if delay:
                        await asyncio.sleep(delay)
                        continue
                    raise RSSFetchError(f"Rate limited (Status {status}).")
                if status >= 400: raise RSSFetchError(f"HTTP Error {status}")
                
                if "ETag" in resp_headers: self.db_service.update_state("rss_etag", resp_headers["ETag"])
                if "Last-Modified" in resp_headers: self.db_service.update_state("rss_modified", resp_headers["Last-Modified"])
                
                entries.extend(self._parse_feed_content(content, parse_rss_entry))
                return entries
            except Exception as e:
                if delay: await asyncio.sleep(delay)
                else: log.warning(f"Feed fetch failed for {RSS_URL}: {e}")
                
        return entries

    def _parse_feed_content(self, content: str, parser_func) -> List[ReleaseData]:
        try:
            feed = feedparser.parse(content)
            entries = []
            for entry in feed.entries:
                try:
                    release = parser_func(entry)
                    entries.append(release)
                except RSSParseError as e:
                    log.warning(f"action=rss_entry_skip error={e}")
            return entries
        except Exception as e:
            raise RSSParseError(f"Failed to parse the feed wrapper: {e}")
