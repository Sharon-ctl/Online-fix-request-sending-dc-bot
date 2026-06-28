import re
from typing import Dict, Any, Optional
from bs4 import BeautifulSoup
from utils.exceptions import RSSParseError

class ReleaseData:
    def __init__(
        self,
        guid: str,
        title: str,
        link: str,
        published: str,
        image_url: Optional[str] = None,
        release_date: Optional[str] = None,
        play_via: Optional[str] = None,
        modes: Optional[str] = None,
        categories: Optional[str] = None,
        source: str = "Online-Fix"
    ):
        self.guid = guid
        self.title = title
        self.link = link
        self.published = published
        self.image_url = image_url
        self.release_date = release_date
        self.play_via = play_via
        self.modes = modes
        self.categories = categories
        self.source = source

    def to_dict(self) -> Dict[str, Any]:
        return {
            "guid": self.guid,
            "title": self.title,
            "link": self.link,
            "published": self.published,
            "image_url": self.image_url,
            "release_date": self.release_date,
            "play_via": self.play_via,
            "modes": self.modes,
            "categories": self.categories,
            "source": self.source
        }

def _extract_detail(soup: BeautifulSoup, label_patterns: list[str]) -> Optional[str]:
    """Helper to extract details based on typical bold labels in the HTML."""
    for pattern in label_patterns:
        # Looking for things like <b>Release date:</b> 2023 or <strong>Play via:</strong> Steam
        elem = soup.find(lambda tag: tag.name in ["b", "strong"] and re.search(pattern, tag.get_text(), re.IGNORECASE))
        if elem and elem.next_sibling:
            val = str(elem.next_sibling).strip()
            # Clean up leading colons or spaces if any
            if val.startswith(":"):
                val = val[1:].strip()
            if val:
                return val
            # Sometimes it's in the parent or next element
            parent_text = elem.parent.get_text(separator=" ", strip=True)
            match = re.search(f"{pattern}\\s*:?\\s*(.+)", parent_text, re.IGNORECASE)
            if match:
                return match.group(1).strip()
    return None

def parse_rss_entry(entry: Dict[str, Any]) -> ReleaseData:
    """Parses a single feedparser entry into a ReleaseData object."""
    try:
        guid = entry.get("id", entry.get("guid", entry.get("link")))
        title = entry.get("title", "Unknown Title")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", "Unknown Date"))
        description = entry.get("description", entry.get("summary", ""))

        if not guid:
            raise RSSParseError("Entry missing GUID/ID")

        # Parse HTML description
        soup = BeautifulSoup(description, "html.parser")
        
        # Extract Image
        image_url = None
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            image_url = img_tag["src"]
            if image_url.startswith("/"):
                image_url = "https://online-fix.me" + image_url

        # Extract textual details
        release_date = _extract_detail(soup, ["Release date", "Дата выхода"])
        play_via = _extract_detail(soup, ["Play via", "Способ игры"])
        modes = _extract_detail(soup, ["Modes", "Жанр", "Режимы"])
        categories = _extract_detail(soup, ["Categories", "Категории"])

        return ReleaseData(
            guid=guid,
            title=title,
            link=link,
            published=published,
            image_url=image_url,
            release_date=release_date,
            play_via=play_via,
            modes=modes,
            categories=categories
        )

    except Exception as e:
        if isinstance(e, RSSParseError):
            raise
        raise RSSParseError(f"Failed to parse RSS entry: {e}")

def parse_html_article(soup: BeautifulSoup) -> ReleaseData:
    """Parses a single DLE HTML article block into a ReleaseData object."""
    try:
        # Extract link
        link_tag = soup.find('a', class_='big-link')
        if not link_tag:
            link_tag = soup.find('a')
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ""
        guid = link
        
        # Extract title
        title_tag = soup.find(lambda tag: tag.name in ['h2', 'h3'])
        title = title_tag.text.strip() if title_tag else "Unknown Title"
        
        # Extract image
        image_url = None
        img_tag = soup.find('img')
        if img_tag:
            image_url = img_tag.get('data-src') or img_tag.get('src')
            if image_url and image_url.startswith("/"):
                image_url = "https://online-fix.me" + image_url
                
        # Extract published date from time tag
        published = "Unknown Date"
        time_tag = soup.find('time')
        if time_tag and 'datetime' in time_tag.attrs:
            published = time_tag['datetime']
            
        # The preview-text acts like the RSS description
        preview = soup.find('div', class_='preview-text')
        
        release_date = None
        play_via = None
        modes = None
        categories = None
        
        if preview:
            release_date = _extract_detail(preview, ["Release date", "Релиз игры", "Дата выхода"])
            play_via = _extract_detail(preview, ["Play via", "Игра через", "Способ игры"])
            modes = _extract_detail(preview, ["Modes", "Жанр", "Режимы"])
            categories = _extract_detail(preview, ["Categories", "Категории"])

        if not guid:
            raise RSSParseError("Article missing GUID/Link")

        return ReleaseData(
            guid=guid,
            title=title,
            link=link,
            published=published,
            image_url=image_url,
            release_date=release_date,
            play_via=play_via,
            modes=modes,
            categories=categories
        )
    except Exception as e:
        if isinstance(e, RSSParseError):
            raise
        raise RSSParseError(f"Failed to parse HTML article: {e}")

def parse_fitgirl_rss_entry(entry: Dict[str, Any]) -> ReleaseData:
    """Parses a single feedparser entry from FitGirl into a ReleaseData object."""
    try:
        guid = entry.get("id", entry.get("guid", entry.get("link")))
        title = entry.get("title", "Unknown Title")
        link = entry.get("link", "")
        published = entry.get("published", entry.get("updated", "Unknown Date"))
        description = entry.get("description", entry.get("summary", ""))

        if not guid:
            raise RSSParseError("Entry missing GUID/ID")

        # Parse HTML description to find image if it exists
        soup = BeautifulSoup(description, "html.parser")
        image_url = None
        img_tag = soup.find("img")
        if img_tag and img_tag.get("src"):
            image_url = img_tag["src"]

        return ReleaseData(
            guid=guid,
            title=title,
            link=link,
            published=published,
            image_url=image_url,
            release_date=None,
            play_via=None,
            modes=None,
            categories=None,
            source="FitGirl"
        )
    except Exception as e:
        raise RSSParseError(f"Failed to parse FitGirl RSS entry: {e}")

def parse_fitgirl_article(soup: BeautifulSoup) -> ReleaseData:
    """Parses a single WordPress HTML article block from FitGirl into a ReleaseData object."""
    try:
        title_tag = soup.find('h1', class_='entry-title')
        if not title_tag:
            title_tag = soup.find('h2', class_='entry-title')
            
        link_tag = title_tag.find('a') if title_tag else None
        
        if not title_tag or not link_tag:
            # Fallback if structure is slightly different
            link_tag = soup.find('a', rel='bookmark')
            title = link_tag.text.strip() if link_tag else "Unknown Title"
        else:
            title = link_tag.text.strip()
            
        link = link_tag['href'] if link_tag and 'href' in link_tag.attrs else ""
        guid = link

        # Extract published date from time tag
        published = "Unknown Date"
        time_tag = soup.find('time', class_='entry-date')
        if time_tag and 'datetime' in time_tag.attrs:
            published = time_tag['datetime']
        elif time_tag:
            published = time_tag.text.strip()

        image_url = None
        img_tag = soup.find('img')
        if img_tag and 'src' in img_tag.attrs:
            image_url = img_tag['src']

        if not guid:
            raise RSSParseError("FitGirl Article missing GUID/Link")

        return ReleaseData(
            guid=guid,
            title=title,
            link=link,
            published=published,
            image_url=image_url,
            release_date=None,
            play_via=None,
            modes=None,
            categories=None,
            source="FitGirl"
        )
    except Exception as e:
        raise RSSParseError(f"Failed to parse FitGirl HTML article: {e}")
