import os
from typing import List
import httpx
from bs4 import BeautifulSoup
from .base import BaseProvider, SearchResult

class BingProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="bing")
        self.api_key = os.getenv("BING_API_KEY")
        self.api_url = "https://api.bing.microsoft.com/v7.0/search"
        self.scrape_url = "https://www.bing.com/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        if self.api_key:
            return await self._search_api(client, query)
        else:
            return await self._search_html(client, query)

    async def _search_api(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        headers = {
            "Ocp-Apim-Subscription-Key": self.api_key
        }
        params = {
            "q": query,
            "count": 10
        }
        
        try:
            response = await client.get(self.api_url, headers=headers, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            web_pages = data.get("webPages", {}).get("value", [])
            results = []
            
            for idx, item in enumerate(web_pages):
                title = item.get("name", "")
                url = item.get("url", "")
                snippet = item.get("snippet", "")
                published_date = item.get("dateLastCrawled")
                
                domain = self.extract_domain(url)
                raw_score = float(max(1.0, 10.0 - idx))
                
                results.append(
                    SearchResult(
                        title=title,
                        url=url,
                        domain=domain,
                        snippet=snippet or "No description available.",
                        source=self.name,
                        published_date=published_date,
                        raw_score=raw_score
                    )
                )
            return results
        except Exception as e:
            print(f"Bing API search failed, falling back to HTML: {e}")
            return await self._search_html(client, query)

    async def _search_html(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        params = {"q": query}
        headers = {
            "User-Agent": "Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36",
            "Accept-Language": "en-US,en;q=0.9"
        }
        
        try:
            response = await client.get(self.scrape_url, params=params, headers=headers, timeout=5.0)
            response.raise_for_status()
            
            soup = BeautifulSoup(response.text, "html.parser")
            algos = soup.find_all("li", class_="b_algo")
            results = []
            seen_urls = set()
            
            for idx, algo in enumerate(algos[:10]):
                h2 = algo.find("h2")
                if not h2:
                    continue
                    
                title_link = h2.find("a")
                if not title_link:
                    continue
                    
                title = title_link.get_text(strip=True)
                url = title_link.get("href", "")
                
                if not url or url.startswith("#") or url.startswith("javascript:") or url in seen_urls:
                    continue
                seen_urls.add(url)
                
                # Extract Snippet
                snippet = ""
                snippet_div = algo.find("div", class_="b_snippet")
                if not snippet_div:
                    caption = algo.find("div", class_="b_caption")
                    if caption:
                        snippet_div = caption.find("p")
                if not snippet_div:
                    snippet_div = algo.find("p")
                    
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
            print(f"Bing HTML scraper failed: {e}")
            return []
