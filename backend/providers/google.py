import os
from typing import List
import httpx
from .base import BaseProvider, SearchResult

class GoogleProvider(BaseProvider):
    def __init__(self):
        super().__init__(name="google")
        self.api_key = os.getenv("GOOGLE_API_KEY")
        self.cx = os.getenv("GOOGLE_CX")
        self.api_url = "https://www.googleapis.com/customsearch/v1"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        # Skip if keys are not configured
        if not self.api_key or not self.cx:
            return []
            
        params = {
            "key": self.api_key,
            "cx": self.cx,
            "q": query,
            "num": 10
        }
        
        try:
            response = await client.get(self.api_url, params=params, timeout=5.0)
            response.raise_for_status()
            data = response.json()
            
            items = data.get("items", [])
            results = []
            
            for idx, item in enumerate(items):
                title = item.get("title", "")
                url = item.get("link", "")
                snippet = item.get("snippet", "")
                
                # Check for published dates inside Google's pagemap metadata
                published_date = None
                pagemap = item.get("pagemap", {})
                metatags = pagemap.get("metatags", [])
                if metatags and isinstance(metatags, list) and len(metatags) > 0:
                    meta = metatags[0]
                    published_date = (
                        meta.get("article:published_time") or 
                        meta.get("datepublished") or 
                        meta.get("pubdate") or
                        meta.get("og:pubdate")
                    )
                
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
            print(f"Google Search failed: {e}")
            return []
