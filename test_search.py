from curl_cffi import requests
from bs4 import BeautifulSoup

def search_game(query: str):
    url = "https://online-fix.me/index.php?do=search"
    # DLE usually uses POST for search
    data = {
        "do": "search",
        "subaction": "search",
        "story": query
    }
    print(f"Searching for {query}...")
    try:
        resp = requests.post(url, data=data, impersonate="chrome110", timeout=15)
        print(f"Status: {resp.status_code}")
        
        soup = BeautifulSoup(resp.text, 'html.parser')
        
        # In DLE, search results might be articles.
        articles = soup.find_all('div', class_='article')
        if not articles:
            articles = soup.find_all('article', class_='article')
            
        with open("search_out.txt", "w", encoding="utf-8") as f:
            f.write(f"Found {len(articles)} potential results.\n")
            for a in articles[:1]:
                f.write(str(a))
    except Exception as e:
        print(f"Error: {e}")

search_game("minecraft")
