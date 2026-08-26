import os
from typing import List
import httpx
from .base import BaseProvider, SearchResult

class BingProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="bing")
        self.api_key = os.getenv("BING_API_KEY")
        self.api_url = "https://api.bing.microsoft.com/v7.0/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        # Skip if keys are not configured
        if not self.api_key:
            return []
            
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
            print(f"Bing Search failed: {e}")
            return []
