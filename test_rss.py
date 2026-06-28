import asyncio
import feedparser

async def main():
    feed = feedparser.parse("https://online-fix.me/rss.xml")
    if feed.entries:
        entry = feed.entries[0]
        print("Enclosures:")
        for enc in entry.get("enclosures", []):
            print(f" - {enc.get('href')}")
        print("Description (first 200 chars):")
        print(entry.get('description', '')[:200])
    else:
        print("No entries.")

if __name__ == "__main__":
    asyncio.run(main())
