from typing import List
import urllib.parse
import httpx
from bs4 import BeautifulSoup
from .base import BaseProvider, SearchResult

class YahooProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="yahoo")
        self.scrape_url = "https://search.yahoo.com/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/121.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            response = await client.get(self.scrape_url, params=params, headers=headers, timeout=5.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            # Yahoo algorithm result cards
            cards = soup.find_all("div", class_=lambda c: c and "algo" in c)
            results = []
            seen_urls = set()
            
            for idx, card in enumerate(cards[:12]):
                # Title link is inside h3 or class title
                link = card.find("a")
                if not link:
                    continue
                    
                title = link.get_text(strip=True)
                url = link.get("href", "")
                
                # Yahoo sometimes wraps direct links in redirect paths /RU=.../RK=2/
                if "/RU=" in url:
                    try:
                        start_idx = url.find("/RU=") + 4
                        end_idx = url.find("/RK=", start_idx)
                        if end_idx != -1:
                            encoded_url = url[start_idx:end_idx]
                            url = urllib.parse.unquote(encoded_url)
                    except Exception:
                        pass
                
                if not url or url.startswith("#") or url.startswith("javascript:") or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Extract Snippet
                snippet = ""
                snippet_div = card.find("div", class_=lambda c: c and "compText" in c)
                if not snippet_div:
                    snippet_div = card.find("p")
                    
                if snippet_div:
                    snippet = snippet_div.get_text(strip=True)
                    
                domain = self.extract_domain(url)
                raw_score = float(max(1.0, 10.0 - idx))
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        domain=domain,
                        snippet=snippet or "No description available.",
                        source=self.name,
                        published_date=None,
                        raw_score=raw_score
                    )
                )
            return results
        except Exception as e:
            print(f"Yahoo HTML scraper failed: {e}")
            return []
