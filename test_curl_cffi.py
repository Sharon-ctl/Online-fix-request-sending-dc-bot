from curl_cffi import requests

def test_cffi(url):
    print(f"Testing {url} with curl_cffi...")
    try:
        resp = requests.get(url, impersonate="chrome110", timeout=15)
        print(f"Status: {resp.status_code}")
        print(f"Length: {len(resp.text)}")
        if "rss" in resp.text[:200].lower():
            print("SUCCESS: Valid RSS found!")
        else:
            print("FAILED: RSS not found in response.")
    except Exception as e:
        print(f"Error: {e}")

test_cffi("https://online-fix.me/rss.xml")
