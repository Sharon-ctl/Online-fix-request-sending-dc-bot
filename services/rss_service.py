import asyncio
import feedparser
from curl_cffi import requests
from typing import List, Optional
from utils.constants import RSS_URL, HTTP_TIMEOUT, HTTP_RETRIES
from utils.logger import log
from utils.exceptions import RSSFetchError, RSSParseError
from utils.parser import parse_rss_entry, ReleaseData
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

    def _sync_fetch(self, headers: dict):
        try:
            response = self.session.get(RSS_URL, headers=headers)
            return response.status_code, response.headers, response.text
        except Exception as e:
            raise RSSFetchError(f"HTTP Fetch failed: {str(e)}")

    def _sync_search(self, query: str):
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
            raise RSSFetchError(f"Search POST failed: {str(e)}")

    def _sync_get_homepage(self):
        try:
            response = self.session.get("https://online-fix.me/")
            return response.status_code, response.text
        except Exception as e:
            raise RSSFetchError(f"Homepage GET failed: {str(e)}")

    async def get_recent_updates(self, limit: int = 50) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        try:
            status, content = await asyncio.to_thread(self._sync_get_homepage)
            if status >= 400:
                raise RSSFetchError(f"HTTP Error {status} fetching homepage")
        except Exception as e:
            log.error(f"action=get_recent_updates_failed error={e}")
            return []
            
        soup = BeautifulSoup(content, 'html.parser')
        articles = soup.find_all('div', class_='article')
        if not articles:
            articles = soup.find_all('article', class_='article')
            
        results = []
        for article in articles[:limit]:
            try:
                res = parse_html_article(article)
                if res:
                    results.append(res)
            except Exception as e:
                log.warning(f"Failed to parse article on homepage: {e}")
                
        return results

    def _sync_fetch_url(self, url: str):
        try:
            response = self.session.get(url)
            return response.status_code, response.text
        except Exception as e:
            raise RSSFetchError(f"URL GET failed: {str(e)}")

    async def get_genre(self, genre: str, limit: int = 50) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        genre_clean = genre.lower().strip()
        url = f"https://online-fix.me/games/{genre_clean}/"
        status, content = await asyncio.to_thread(self._sync_fetch_url, url)
        
        if status >= 400:
            # Fallback to standard search if category page doesn't exist
            return await self.search_games(genre, limit)
            
        soup = BeautifulSoup(content, 'html.parser')
        articles = soup.find_all('div', class_='article')
        if not articles:
            articles = soup.find_all('article', class_='article')
            
        results = []
        for article in articles[:limit]:
            try:
                res = parse_html_article(article)
                if res:
                    results.append(res)
            except Exception:
                pass
        return results

    async def get_trending(self, limit: int = 20) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        status, content = await asyncio.to_thread(self._sync_get_homepage)
        if status >= 400:
            return await self.get_recent_updates(limit)
            
        soup = BeautifulSoup(content, 'html.parser')
        
        # Try to find the popular games block first
        trending_results = []
        popular_blocks = soup.find_all('div', class_='top-news')
        if not popular_blocks:
            popular_blocks = soup.find_all('ul', class_='top-news')
            
        for block in popular_blocks:
            articles = block.find_all('a')
            for a in articles:
                if 'href' in a.attrs and len(a.text.strip()) > 3:
                    # Fake a ReleaseData for popular link
                    trending_results.append(ReleaseData(
                        title=a.text.strip(),
                        link=a['href'],
                        published="",
                        release_date="",
                        play_via="",
                        modes="",
                        categories=""
                    ))
                    
        if trending_results:
            return trending_results[:limit]
            
        # Fallback to recent updates if popular block isn't found
        return await self.get_recent_updates(limit)

    async def search_games(self, query: str, limit: int = 5) -> List[ReleaseData]:
        from bs4 import BeautifulSoup
        from utils.parser import parse_html_article
        
        try:
            log.debug(f"Searching for {query}")
            status, content = await asyncio.to_thread(self._sync_search, query)
            
            if status >= 400:
                raise RSSFetchError(f"HTTP Error {status} during search")
                
            soup = BeautifulSoup(content, 'html.parser')
            articles = soup.find_all('div', class_='article')
            if not articles:
                articles = soup.find_all('article', class_='article')
                
            results = []
            for article in articles[:limit]:
                try:
                    res = parse_html_article(article)
                    if res:
                        results.append(res)
                except Exception as e:
                    log.warning(f"Failed to parse search result article: {e}")
                    
            return results
            
        except Exception as e:
            log.warning(f"action=search_failed error={e} query={query}")
            raise RSSFetchError(f"Failed to search for {query}: {e}")

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
                
                # Execute blocking curl_cffi in background thread
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
