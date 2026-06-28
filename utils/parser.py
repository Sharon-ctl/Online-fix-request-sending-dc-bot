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
            "categories": self.categories
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
