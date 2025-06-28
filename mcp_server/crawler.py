import requests
from bs4 import BeautifulSoup


def extract_text_from_url(url):
    try:
        resp = requests.get(url, timeout=5)
        soup = BeautifulSoup(resp.text, "html.parser")
        texts = [p.get_text().strip() for p in soup.find_all("p")]
        return "\n".join(texts[:20])  # Limit for MVP
    except Exception as e:
        print(f"Error fetching {url}: {e}")
        return ""
