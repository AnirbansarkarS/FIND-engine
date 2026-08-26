import urllib.parse
from typing import List
from bs4 import BeautifulSoup
import httpx
from .base import BaseProvider, SearchResult

class DuckDuckGoProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="duckduckgo")
        self.search_url = "https://lite.duckduckgo.com/lite/"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        # DDG Lite accepts search query in POST data 'q'
        data = {
            "q": query,
            "kl": "us-en"
        }
        
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Content-Type": "application/x-www-form-urlencoded"
        }
        
        try:
            response = await client.post(self.search_url, data=data, headers=headers, timeout=5.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            links = soup.find_all("a", class_="result-link")
            results = []
            
            for idx, link in enumerate(links[:15]):  # Process up to 15 results
                title = link.get_text(strip=True)
                href = link.get("href", "")
                
                # Parse and decode direct URL from DDG redirect wrapper
                if "uddg=" in href:
                    try:
                        parsed_href = urllib.parse.urlparse(href)
                        queries = urllib.parse.parse_qs(parsed_href.query)
                        if "uddg" in queries:
                            href = queries["uddg"][0]
                    except Exception:
                        pass
                
                if href.startswith("//"):
                    href = "https:" + href
                elif href.startswith("/"):
                    href = "https://duckduckgo.com" + href
                
                # In DDG Lite HTML, the snippet is in the next <tr> following the title <tr>
                snippet = ""
                parent_tr = link.find_parent("tr")
                if parent_tr:
                    next_tr = parent_tr.find_next_sibling("tr")
                    if next_tr and "result-snippet" in next_tr.get("class", []):
                        snippet = next_tr.get_text(strip=True)
                
                snippet = " ".join(snippet.split())
                domain = self.extract_domain(href)
                raw_score = float(max(1.0, 10.0 - idx))
                
                results.append(
                    SearchResult(
                        title=title,
                        url=href,
                        domain=domain,
                        snippet=snippet or "No description available.",
                        source=self.name,
                        published_date=None,
                        raw_score=raw_score
                    )
                )
            return results
        except Exception as e:
            print(f"DuckDuckGo search failed: {e}")
            return []
