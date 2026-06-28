import requests

def test_proxy(url):
    print(f"Testing {url}...")
    try:
        resp = requests.get(url, timeout=10)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)}")
        if "rss" in resp.text[:200].lower():
            print("SUCCESS: Valid RSS found!")
        else:
            print("FAILED: RSS not found in response.")
    except Exception as e:
        print(f"Error: {e}")
    print("-" * 20)

target = "https://online-fix.me/rss.xml"
test_proxy(f"https://api.allorigins.win/get?url={target}")
test_proxy(f"https://corsproxy.io/?{target}")
