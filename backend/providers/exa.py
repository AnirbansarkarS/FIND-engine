import os
import logging
from typing import List
import httpx
from .base import BaseProvider, SearchResult

logger = logging.getLogger("findengine.providers.exa")

class ExaProvider(BaseProvider):
    def __init__(self):
        super().__init__("exa")
        self.api_key = os.getenv("EXA_API_KEY", "").strip()
        self.api_url = "https://api.exa.ai/search"

    async def search(self, client: httpx.AsyncClient, query: str) -> List[SearchResult]:
        if not self.api_key:
            logger.info("EXA_API_KEY is not set. Skipping Exa search provider.")
            return []

        headers = {
            "x-api-key": self.api_key,
            "Content-Type": "application/json",
            "accept": "application/json"
        }
        
        payload = {
            "query": query,
            "type": "auto",
            "numResults": 10,
            "contents": {
                "highlights": True
            }
        }

        try:
            response = await client.post(
                self.api_url,
                headers=headers,
                json=payload,
                timeout=8.0
            )

            if response.status_code != 200:
                logger.warning(f"Exa API returned HTTP {response.status_code}: {response.text}")
                return []

            data = response.json()
            raw_results = data.get("results", [])
            results: List[SearchResult] = []

            for item in raw_results:
                title = item.get("title") or item.get("url") or "Exa Result"
                url = item.get("url", "")
                if not url:
                    continue

                domain = self.extract_domain(url)
                
                # Extract highlights as snippet text
                highlights = item.get("highlights", [])
                if isinstance(highlights, list) and len(highlights) > 0:
                    snippet = " ... ".join(highlights[:2])
                else:
                    snippet = item.get("snippet") or title

                published_date = item.get("publishedDate") or item.get("published_date")
                score = float(item.get("score") or 1.0) * 10.0  # Scale score to ~10 max

                results.append(
                    SearchResult(
                        title=title.strip(),
                        url=url.strip(),
                        domain=domain,
                        snippet=snippet.strip(),
                        source="exa",
                        published_date=published_date,
                        raw_score=min(10.0, score)
                    )
                )

            return results

        except Exception as e:
            logger.error(f"Exa search query failed: {e}")
            return []
